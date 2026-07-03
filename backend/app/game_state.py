import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.models import (
    ActionType,
    BeliefRecord,
    EventRecord,
    FactionMood,
    Location,
    NpcState,
    RelationshipType,
)
from app.world_data import (
    ACTION_EFFECTS,
    FACTION_DATA,
    NPC_DATA,
    SOCIAL_EDGES,
)


class GameStateManager:
    """In-memory game state for the current session.

    This is the single source of truth for:
    - NPC emotional states (trust/fear/respect/anger)
    - Faction moods
    - Known events
    - NPC beliefs

    Cognee Cloud is the DURABLE layer. This is the FAST layer for the game loop.
    On startup, we try to hydrate from Cognee. On every action, we update both.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.player_location: Location = Location.town_square
        self.npcs: Dict[str, NpcState] = {}
        self.factions: Dict[str, FactionMood] = {}
        self.events: List[EventRecord] = []
        self.beliefs: Dict[str, List[BeliefRecord]] = {}  # npc_name -> beliefs
        self.social_graph: Dict[str, List[Tuple[str, RelationshipType, int]]] = (
            {}
        )  # npc_name -> [(other_npc, rel_type, trust)]
        self._init_npcs()
        self._init_factions()
        self._init_social_graph()

    def _init_npcs(self):
        for name, data in NPC_DATA.items():
            self.npcs[name] = NpcState(
                name=name,
                location=data["location"],
                faction=data["faction"],
                trust=data["initial_trust"],
                fear=data["initial_fear"],
                respect=data["initial_respect"],
                anger=data["initial_anger"],
            )
            self.beliefs[name] = []

    def _init_factions(self):
        for faction, data in FACTION_DATA.items():
            self.factions[faction.value] = FactionMood(
                faction=faction,
                trust=data["initial_trust"],
                fear=data["initial_fear"],
                respect=data["initial_respect"],
                anger=data["initial_anger"],
                last_event=None,
            )

    def _init_social_graph(self):
        for edge in SOCIAL_EDGES:
            if len(edge) == 1:
                # NPC with no connections
                self.social_graph[edge[0]] = []
                continue
            npc1, npc2, rel_type, trust = edge
            if npc1 not in self.social_graph:
                self.social_graph[npc1] = []
            if npc2 not in self.social_graph:
                self.social_graph[npc2] = []
            self.social_graph[npc1].append((npc2, rel_type, trust))
            self.social_graph[npc2].append((npc1, rel_type, trust))

    def create_event(
        self,
        action_type: ActionType,
        target_npc: str,
        item: Optional[str],
        description: Optional[str],
        witnesses: List[str],
    ) -> EventRecord:
        # ActionType.help_.value resolves to "help" — matches the key in ACTION_EFFECTS
        effects = ACTION_EFFECTS.get(action_type.value, {})
        event = EventRecord(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            action_type=action_type,
            actor="player",
            target_npc=target_npc,
            item=item,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            location=self.player_location,
            witnesses=witnesses,
            public=effects.get("public", True),
        )
        self.events.append(event)
        return event

    def get_connected_npcs(
        self, npc_name: str
    ) -> List[Tuple[str, RelationshipType, int]]:
        """Returns list of (connected_npc_name, relationship_type, trust_level)."""
        return self.social_graph.get(npc_name, [])

    def get_npcs_for_propagation(self, witness: str, event_id: str) -> List[str]:
        """Determine which NPCs should learn about an event from this witness.

        Uses the social graph to find connected NPCs and the propagation rules.
        """
        candidates = []
        for connected_npc, _rel_type, _trust in self.get_connected_npcs(witness):
            # Skip if this NPC already knows
            if self._npc_knows_event(connected_npc, event_id):
                continue
            candidates.append(connected_npc)
        return candidates

    def _npc_knows_event(self, npc_name: str, event_id: str) -> bool:
        for belief in self.beliefs.get(npc_name, []):
            if belief.event_id == event_id:
                return True
        return False

    def add_belief(self, npc_name: str, belief: BeliefRecord):
        if npc_name not in self.beliefs:
            self.beliefs[npc_name] = []
        # Update existing belief or add new one
        for i, b in enumerate(self.beliefs[npc_name]):
            if b.event_id == belief.event_id:
                self.beliefs[npc_name][i] = belief
                return
        self.beliefs[npc_name].append(belief)

    def get_state_dict(self) -> dict:
        """Return the full game state as a dict for API responses."""
        beliefs_by_npc = {}
        for npc_name, beliefs in self.beliefs.items():
            beliefs_by_npc[npc_name] = [b.model_dump() for b in beliefs]

        return {
            "player_location": self.player_location.value,
            "npcs": {n: s.model_dump() for n, s in self.npcs.items()},
            "factions": {f: m.model_dump() for f, m in self.factions.items()},
            "recent_events": [e.model_dump() for e in self.events[-10:]],
            "session_id": self.session_id,
            "beliefs": beliefs_by_npc,
        }
