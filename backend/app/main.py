import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    ActionRequest,
    ActionResponse,
    DialogueResponse,
    GameStateResponse,
    MemoryGraphResponse,
    MemoryGraphNode,
    MemoryGraphEdge,
    EventRecord,
    BeliefRecord,
    ActionType,
    MemoryMode,
    Faction,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.cognee_client import cognee_client

    await cognee_client.connect()
    print("Cognee Cloud connected")
    yield
    await cognee_client.disconnect()
    print("Cognee Cloud disconnected")


app = FastAPI(title="Echo Game API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Session Management ─────────────────────────────────────────

from app.game_state import GameStateManager
from app.cognee_client import cognee_client
from app.propagation import PropagationEngine
from app.dialogue import DialogueComposer
from app.baselines import BaselineService

_active_sessions: dict[str, GameStateManager] = {}
_propagation_engines: dict[str, PropagationEngine] = {}
_dialogue_composers: dict[str, DialogueComposer] = {}
_baseline_services: dict[str, BaselineService] = {}


def _get_or_create_session(session_id: str | None = None) -> str:
    """Get or create a game session. Returns the session ID."""
    if session_id and session_id in _active_sessions:
        return session_id
    sid = session_id or f"session_{uuid.uuid4().hex[:8]}"
    gs = GameStateManager(sid)

    # Build the per-session services
    _active_sessions[sid] = gs
    _propagation_engines[sid] = PropagationEngine(gs, cognee_client)
    _dialogue_composers[sid] = DialogueComposer(gs, cognee_client)
    _baseline_services[sid] = BaselineService(gs, cognee_client)

    return sid


# ─── Health ──────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ─── Game State ──────────────────────────────────────────────────


@app.get("/api/state", response_model=GameStateResponse)
def get_state(session_id: str = Query(default=None)):
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    state = gs.get_state_dict()
    return GameStateResponse(**state)


# ─── Action ──────────────────────────────────────────────────────


@app.post("/api/action", response_model=ActionResponse)
async def perform_action(
    req: ActionRequest,
    session_id: str = Query(default=None),
):
    """Player performs an action.

    This is the MAIN game loop entry point. It:
    1. Records the event in local game state
    2. Determines witnesses (NPCs at the same location)
    3. Writes the event to Cognee Cloud (background, non-blocking)
    4. Propagates through the social graph (background)
    5. Updates NPC sentiment
    6. Generates NPC reactions
    7. Returns the updated state and dialogue

    The game loop NEVER blocks on Cognee writes. Cognee calls run in
    background async tasks. The player sees their immediate reaction based
    on local state, while Cognee syncs durably in the background.
    """
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    prop = _propagation_engines[sid]
    dialogue = _dialogue_composers[sid]

    # Step 1: Determine witnesses
    target_npc_obj = gs.npcs.get(req.target_npc)
    witnesses = [
        name
        for name, npc in gs.npcs.items()
        if npc.location == gs.player_location and name != req.target_npc
    ]
    # The target NPC always witnesses if they're at their location
    if target_npc_obj and req.target_npc not in witnesses:
        witnesses.append(req.target_npc)

    # Step 2: Create the event
    event = gs.create_event(
        action_type=req.action_type,
        target_npc=req.target_npc,
        item=req.item,
        description=req.description,
        witnesses=witnesses,
    )

    # Step 3: Synchronously add witness beliefs to local state
    # so NPC reactions are informed by what they witnessed.
    for witness_name in witnesses:
        witness_belief = BeliefRecord(
            npc_name=witness_name,
            event_id=event.event_id,
            certainty=1.0,
            source="witnessed",
            heard_from=None,
        )
        gs.add_belief(witness_name, witness_belief)

    # Step 4: Background propagation (Cognee writes + social spread)
    import asyncio

    asyncio.create_task(prop.propagate_event(event))

    # Step 5: Generate NPC reactions based on local knowledge
    npc_reactions = {}
    for npc_name in gs.npcs:
        reaction = await dialogue.generate_reaction(
            npc_name=npc_name,
            event=event,
            mode="hybrid",
        )
        npc_reactions[npc_name] = reaction

    return ActionResponse(
        event_id=event.event_id,
        npc_reactions=npc_reactions,
        updated_state=gs.get_state_dict(),
    )


# ─── Dialogue ────────────────────────────────────────────────────


@app.get("/api/dialogue/{npc_name}", response_model=DialogueResponse)
async def get_dialogue(
    npc_name: str,
    mode: MemoryMode = MemoryMode.hybrid,
    session_id: str = Query(default=None),
):
    """Get an NPC's reaction to the current situation.

    This endpoint demonstrates the three memory modes:
    - graph: Only factual graph knowledge (no semantic generalization)
    - vector: Only semantic similarity (no structural knowledge boundaries)
    - hybrid: Both factual graph + semantic meaning
    """
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    baseline = _baseline_services[sid]

    if npc_name not in gs.npcs:
        raise HTTPException(status_code=404, detail=f"NPC '{npc_name}' not found")

    dialogue, provenance = await baseline.get_dialogue_with_provenance(
        npc_name=npc_name,
        mode=mode,
    )

    return DialogueResponse(
        npc_name=npc_name,
        dialogue=dialogue,
        provenance=provenance,
        mode=mode,
    )


# ─── Memory Graph ────────────────────────────────────────────────


@app.get("/api/memory/graph", response_model=MemoryGraphResponse)
def get_memory_graph(session_id: str = Query(default=None)):
    """Get the memory graph data for the visualization panel.

    Returns nodes and edges that the frontend renders as an animated graph.
    This powers the 'who knows what' visualization.
    """
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]

    nodes: list[MemoryGraphNode] = []
    edges: list[MemoryGraphEdge] = []

    # Player node
    nodes.append(MemoryGraphNode(id="player", label="Player", type="player"))

    # NPC nodes
    for name, npc in gs.npcs.items():
        nodes.append(
            MemoryGraphNode(
                id=name,
                label=name,
                type="npc",
                faction=npc.faction,
            )
        )

    # Faction nodes
    for faction_name in gs.factions:
        nodes.append(
            MemoryGraphNode(
                id=faction_name,
                label=faction_name,
                type="faction",
            )
        )

    # Event nodes
    for event in gs.events:
        nodes.append(
            MemoryGraphNode(
                id=event.event_id,
                label=f"{event.action_type.value}:{event.event_id[-4:]}",
                type="event",
            )
        )
        edges.append(
            MemoryGraphEdge(
                source="player",
                target=event.event_id,
                label="performed",
            )
        )

    # Belief edges
    for npc_name, beliefs in gs.beliefs.items():
        for belief in beliefs:
            edges.append(
                MemoryGraphEdge(
                    source=npc_name,
                    target=belief.event_id,
                    label=f"knows ({belief.certainty:.0%})",
                )
            )

    # Social edges (deduplicated)
    seen_edges: set[tuple[str, str]] = set()
    for npc_name, connections in gs.social_graph.items():
        for other_name, rel_type, trust in connections:
            edge_key = tuple(sorted([npc_name, other_name]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append(
                    MemoryGraphEdge(
                        source=npc_name,
                        target=other_name,
                        label=f"{rel_type.value} ({trust})",
                    )
                )

    return MemoryGraphResponse(nodes=nodes, edges=edges)


# ─── Memory Events ───────────────────────────────────────────────


@app.get("/api/memory/events")
def get_memory_events(session_id: str = Query(default=None)):
    """Get all known events with their details."""
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    return {"events": [e.model_dump() for e in gs.events]}


# ─── Memory Beliefs ──────────────────────────────────────────────


@app.get("/api/memory/beliefs")
def get_memory_beliefs(session_id: str = Query(default=None)):
    """Get all NPC beliefs with certainty levels."""
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    return {
        "beliefs": {
            name: [b.model_dump() for b in beliefs]
            for name, beliefs in gs.beliefs.items()
        }
    }


# ─── Faction Moods ───────────────────────────────────────────────


@app.get("/api/memory/factions")
def get_faction_moods(session_id: str = Query(default=None)):
    """Get faction sentiment meters."""
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    return {"factions": {f: m.model_dump() for f, m in gs.factions.items()}}


# ─── Classify Action ─────────────────────────────────────────────


@app.post("/api/classify")
async def classify_action(req: ActionRequest):
    """Classify a novel action using Cognee vector similarity.

    This is the anti-hardcode proof. The player types anything they want
    and Cognee classifies it by similarity to known action archetypes.
    """
    if not req.description:
        return {
            "action_type": req.action_type.value,
            "valence": "neutral",
            "is_novel": False,
        }

    result = await cognee_client.classify_action(req.description)
    return {
        **result,
        "is_novel": True,
        "original_action": req.action_type.value,
    }


# ─── Reset ────────────────────────────────────────────────────────


@app.post("/api/reset")
def reset_session(session_id: str = Query(default=None)):
    """Reset the game session. Clears all local state."""
    if session_id and session_id in _active_sessions:
        del _active_sessions[session_id]
        _propagation_engines.pop(session_id, None)
        _dialogue_composers.pop(session_id, None)
        _baseline_services.pop(session_id, None)

    new_sid = _get_or_create_session()
    gs = _active_sessions[new_sid]

    return {
        "status": "reset",
        "session_id": new_sid,
        "state": gs.get_state_dict(),
    }
