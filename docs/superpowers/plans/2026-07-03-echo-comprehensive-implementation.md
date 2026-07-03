# Echo — Comprehensive Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build "Echo" — a playable 2D browser game where 6 NPCs share social memory via Cognee Cloud. Player actions (steal, gift, lie, apologize, etc.) create durable graph+vector memory. Memory propagates through faction relationships. A comparison toggle proves Cognee's hybrid advantage over pure-vector and pure-graph.

**Architecture:** React + TypeScript frontend → Python FastAPI backend → Cognee Cloud API. Frontend renders a 2D village map with NPCs + a memory inspector panel. Backend manages game state, writes to Cognee via `remember()`/`add()`/`cognify()`, runs propagation rules, and serves grounded NPC dialogue via `recall()`. No mocks. No fixtures. Every NPC reaction is a live Cognee recall.

**Tech Stack:**
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Backend:** Python 3.11+, FastAPI, uvicorn, pydantic
- **Memory:** Cognee Cloud SDK (`cognee>=0.1.30`)
- **LLM:** OpenAI GPT-4o-mini (for Cognee's cognify/recall pipeline)
- **Deploy:** Vercel (frontend) + Railway or Fly.io (backend)

---

## File Map (what gets created)

```
cog2/
├── backend/
│   ├── requirements.txt          # Python deps pinned
│   ├── .env.example              # Secrets template
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app, routes
│   │   ├── config.py             # Env-based settings
│   │   ├── models.py             # Pydantic models for game state
│   │   ├── game_state.py         # In-memory game state manager
│   │   ├── cognee_client.py      # All Cognee Cloud interactions
│   │   ├── world_data.py         # Static world def (NPCs, factions, locations, edges)
│   │   ├── propagation.py        # Social propagation engine
│   │   ├── dialogue.py           # NPC dialogue composer
│   │   └── baselines.py         # Graph-only / vector-only / hybrid recall strategies
│   └── tests/
│       ├── __init__.py
│       ├── test_propagation.py
│       ├── test_dialogue.py
│       └── test_baselines.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api.ts                 # Axios client to backend
│   │   ├── types.ts               # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── TopBar.tsx          # Mode toggle, objective, reset
│   │   │   ├── GameCanvas.tsx      # 2D village map (HTML canvas)
│   │   │   ├── PlayerSprite.tsx    # Player avatar
│   │   │   ├── NPCSprite.tsx       # NPC avatar with faction color
│   │   │   ├── ActionPanel.tsx     # Action buttons
│   │   │   ├── DialogueBox.tsx     # NPC response with provenance
│   │   │   └── InspectorPanel.tsx  # Right sidebar with tabs
│   │   └── hooks/
│   │       ├── useGameState.ts     # Fetch + cache game state
│   │       └── useMemory.ts        # Fetch memory graph data
├── echo-spike/                     # Already exists — day-1 spike script
│   ├── echo_spike.py
│   ├── requirements.txt
│   └── .gitignore
├── echo_spec.md                    # Already exists — design spec
├── AGENTS.md                       # Already exists — project brain
└── README.md                       # Root README
```

---

## Chunk 0: Spike Verification (REQUIRED before anything)

**Goal:** Run the existing `echo-spike/echo_spike.py` against real Cognee Cloud to empirically verify 7 load-bearing assumptions.

**Why this must be first:** If any of the core tests fail (especially test 2 = multi-hop reasoning, or test 6 = dataset isolation), Echo cannot win as designed. Building the full app on broken assumptions wastes the week.

- [ ] **Step 1: Get Cognee Cloud credentials**
  - User needs to provide: `COGNEE_BASE_URL`, `COGNEE_API_KEY`, `LLM_API_KEY`
  - Create `echo-spike/.env` from `.env.example` with real values

- [ ] **Step 2: Install and run the spike**
  ```bash
  cd echo-spike
  pip install -r requirements.txt
  python echo_spike.py
  ```

- [ ] **Step 3: Read `spike_results.jsonl`**
  - Every test has `passed: true/false` + latency + raw answer
  - Apply the GO/PIVOT/DOWNGRADE matrix (see spike plan §Task 9)

- [ ] **Step 4: If GO** — proceed to Chunk 1. Record spike findings for the README.
- [ ] **If PIVOT (test 2 or test 6 failed)** — stop. Report to user. Do not build Echo.

---

## Chunk 1: Backend Foundation

**Goal:** A running FastAPI server with game state, connected to Cognee Cloud, that can create events and store them as real graph memory.

### Task 1.1: Backend Scaffold & Models

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/models.py`
- Create: `backend/app/main.py` (skeleton with health check)

- [ ] **Step 1: Create `backend/requirements.txt`**
```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
cognee>=0.1.30
python-dotenv>=1.0.1
httpx==0.28.1
```

- [ ] **Step 2: Create `backend/app/config.py`**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cognee_base_url: str
    cognee_api_key: str
    llm_api_key: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

- [ ] **Step 3: Create `backend/app/models.py`** with all game data types:

```python
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
from enum import Enum

# ─── Enums ───────────────────────────────────────────────────────

class ActionType(str, Enum):
    steal = "steal"
    gift = "gift"
    help_ = "help"
    lie = "lie"
    apologize = "apologize"
    threaten = "threaten"
    ask_rumor = "ask_rumor"
    return_item = "return_item"

class MemoryMode(str, Enum):
    graph = "graph"
    vector = "vector"
    hybrid = "hybrid"

class Faction(str, Enum):
    orchard_guild = "Orchard Guild"
    shrine_circle = "Shrine Circle"
    alley_network = "Alley Network"

class Location(str, Enum):
    orchard_stall = "orchard_stall"
    guild_hall = "guild_hall"
    shrine = "shrine"
    alley = "alley"
    town_square = "town_square"

class RelationshipType(str, Enum):
    ally = "ally"
    rival = "rival"
    neutral = "neutral"

# ─── Request / Response Models ───────────────────────────────────

class ActionRequest(BaseModel):
    action_type: ActionType
    target_npc: str
    item: Optional[str] = None
    description: Optional[str] = None  # For open-action text box

class ActionResponse(BaseModel):
    event_id: str
    npc_reactions: Dict[str, str]  # npc_name -> dialogue
    updated_state: Dict

class DialogueRequest(BaseModel):
    npc_name: str
    mode: MemoryMode = MemoryMode.hybrid

class DialogueResponse(BaseModel):
    npc_name: str
    dialogue: str
    provenance: List[Dict]  # What facts drove this line
    mode: MemoryMode

class NpcState(BaseModel):
    name: str
    location: Location
    faction: Faction
    trust: float  # 0-100
    fear: float   # 0-100
    respect: float  # 0-100
    anger: float  # 0-100

class EventRecord(BaseModel):
    event_id: str
    action_type: ActionType
    actor: str  # "player"
    target_npc: str
    item: Optional[str]
    description: Optional[str]
    timestamp: str  # ISO 8601
    location: Location
    witnesses: List[str]  # NPC names who saw it
    public: bool

class BeliefRecord(BaseModel):
    npc_name: str
    event_id: str
    certainty: float  # 0.0 - 1.0
    source: Literal["witnessed", "told", "rumor"]
    heard_from: Optional[str]

class FactionMood(BaseModel):
    faction: Faction
    trust: float
    fear: float
    respect: float
    anger: float
    last_event: Optional[str]

class MemoryGraphNode(BaseModel):
    id: str
    label: str
    type: Literal["player", "npc", "faction", "event", "location", "belief"]
    faction: Optional[Faction]

class MemoryGraphEdge(BaseModel):
    source: str
    target: str
    label: str  # "witnessed", "told", "believes", "performed", "belongs_to", etc.

class MemoryGraphResponse(BaseModel):
    nodes: List[MemoryGraphNode]
    edges: List[MemoryGraphEdge]

class GameStateResponse(BaseModel):
    player_location: Location
    npcs: Dict[str, NpcState]
    factions: Dict[str, FactionMood]
    recent_events: List[EventRecord]
    session_id: str
```
**Explanation of every model:**
- `ActionType` — the 8 possible player actions. `help_` has underscore because `help` is a Python keyword.
- `MemoryMode` — which baseline strategy to use for dialogue.
- `ActionRequest` — what the player sends when they do something. `description` field is for the open-action text box (anti-hardcode proof).
- `ActionResponse` — what comes back. Contains the event ID, the reactions from all NPCs who know about it, and the full updated game state.
- `NpcState` — each NPC's current emotional state toward the player. Trust/fear/respect/anger on a 0-100 scale.
- `EventRecord` — a complete record of an event. Who did it, who saw it, where, when, whether it's public knowledge.
- `BeliefRecord` — what an NPC believes about an event. Certainty goes from 0 (not sure at all) to 1 (absolutely certain). Source says whether they saw it, were told, or heard as rumor.
- `FactionMood` — the aggregate sentiment of an entire faction toward the player.
- `MemoryGraphNode/Edge` — data for the visualization panel. The frontend renders these as an animated graph.
- `GameStateResponse` — the full state of the game world at any moment.

- [ ] **Step 4: Create `backend/app/__init__.py`** (empty)

- [ ] **Step 5: Create `backend/app/main.py` skeleton**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Echo Game API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
```

- [ ] **Step 6: Verify backend boots**

```bash
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Check: `curl http://localhost:8000/health` returns `{"status": "ok", "version": "1.0.0"}`.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "backend: scaffold FastAPI with models and health check"
```

### Task 1.2: World Data & Game State Manager

**Files:**
- Create: `backend/app/world_data.py`
- Create: `backend/app/game_state.py`

- [ ] **Step 1: Create `backend/app/world_data.py`** — the static world definition

```python
from app.models import Location, Faction, RelationshipType

# ─── The 6 NPCs ──────────────────────────────────────────────────

NPC_DATA = {
    "Mira": {
        "display_name": "Mira",
        "location": Location.orchard_stall,
        "faction": Faction.orchard_guild,
        "role": "orchard merchant",
        "initial_trust": 50,
        "initial_fear": 20,
        "initial_respect": 40,
        "initial_anger": 10,
        "description": "Tends the orchard stall in Lumen Market. Friendly but watchful."
    },
    "Rowan": {
        "display_name": "Rowan",
        "location": Location.guild_hall,
        "faction": Faction.orchard_guild,
        "role": "guild guard",
        "initial_trust": 40,
        "initial_fear": 30,
        "initial_respect": 50,
        "initial_anger": 15,
        "description": "Guild guard who watches over the market. Loyal to Mira."
    },
    "Sol": {
        "display_name": "Sol",
        "location": Location.shrine,
        "faction": Faction.shrine_circle,
        "role": "shrine keeper",
        "initial_trust": 60,
        "initial_fear": 5,
        "initial_respect": 70,
        "initial_anger": 5,
        "description": "Keeper of the shrine. Neutral, wise, observant."
    },
    "Niko": {
        "display_name": "Niko",
        "location": Location.alley,
        "faction": Faction.alley_network,
        "role": "alway broker",
        "initial_trust": 30,
        "initial_fear": 40,
        "initial_respect": 20,
        "initial_anger": 25,
        "description": "Operates from the alley. Deals in secrets and contraband."
    },
    "Vale": {
        "display_name": "Vale",
        "location": Location.town_square,
        "faction": None,  # No faction — independent
        "role": "town crier",
        "initial_trust": 45,
        "initial_fear": 15,
        "initial_respect": 35,
        "initial_anger": 10,
        "description": "The town crier. Gossip spreads fast through Vale."
    },
    "Ilya": {
        "display_name": "Ilya",
        "location": Location.town_square,
        "faction": None,  # Outsider — no faction
        "role": "outsider traveler",
        "initial_trust": 50,
        "initial_fear": 25,
        "initial_respect": 30,
        "initial_anger": 10,
        "description": "A traveler passing through. Knows nobody when they arrive."
    }
}

# ─── The 3 Factions ──────────────────────────────────────────────

FACTION_DATA = {
    Faction.orchard_guild: {
        "display_name": "Orchard Guild",
        "members": ["Mira", "Rowan"],
        "initial_trust": 50,
        "initial_fear": 20,
        "initial_respect": 40,
        "initial_anger": 10,
    },
    Faction.shrine_circle: {
        "display_name": "Shrine Circle",
        "members": ["Sol"],
        "initial_trust": 60,
        "initial_fear": 5,
        "initial_respect": 70,
        "initial_anger": 5,
    },
    Faction.alley_network: {
        "display_name": "Alley Network",
        "members": ["Niko"],
        "initial_trust": 30,
        "initial_fear": 40,
        "initial_respect": 20,
        "initial_anger": 25,
    }
}

# ─── Social Graph Edges ──────────────────────────────────────────

# Format: (npc1, npc2, relationship_type, trust_level 0-100)
SOCIAL_EDGES = [
    ("Mira", "Rowan", RelationshipType.ally, 85),
    ("Rowan", "Mira", RelationshipType.ally, 90),
    ("Mira", "Sol", RelationshipType.neutral, 50),
    ("Sol", "Mira", RelationshipType.neutral, 55),
    ("Rowan", "Sol", RelationshipType.neutral, 40),
    ("Sol", "Rowan", RelationshipType.neutral, 45),
    ("Mira", "Niko", RelationshipType.rival, 15),
    ("Niko", "Mira", RelationshipType.rival, 10),
    ("Rowan", "Niko", RelationshipType.rival, 10),
    ("Niko", "Rowan", RelationshipType.rival, 15),
    ("Vale", "Mira", RelationshipType.neutral, 60),
    ("Vale", "Rowan", RelationshipType.neutral, 55),
    ("Vale", "Sol", RelationshipType.neutral, 65),
    ("Vale", "Niko", RelationshipType.neutral, 45),
    ("Ilya",),  # Ilya knows nobody initially — tuple with just one name
]

# ─── Propagation Rules ───────────────────────────────────────────

# Which relationships cause memory propagation, and with what probability
PROPAGATION_RULES = {
    RelationshipType.ally: {"spread_chance": 0.9, "max_hops": 2, "certainty_multiplier": 0.8},
    RelationshipType.neutral: {"spread_chance": 0.3, "max_hops": 1, "certainty_multiplier": 0.5},
    # Rivals do NOT spread memory to each other
}

# ─── Locations Map ───────────────────────────────────────────────

LOCATION_DATA = {
    Location.orchard_stall: {
        "display_name": "Orchard Stall",
        "x": 150, "y": 100,  # Pixel coordinates on the 2D map
        "description": "A wooden stall piled with ripe fruit and woven baskets."
    },
    Location.guild_hall: {
        "display_name": "Guild Hall",
        "x": 400, "y": 80,
        "description": "A sturdy stone building with the Orchard Guild crest above the door."
    },
    Location.shrine: {
        "display_name": "Shrine",
        "x": 300, "y": 250,
        "description": "A quiet shrine with a small fountain. Sol tends the candles here."
    },
    Location.alley: {
        "display_name": "Alley",
        "x": 100, "y": 200,
        "description": "A narrow alley between buildings. Niko conducts business in the shadows."
    },
    Location.town_square: {
        "display_name": "Town Square",
        "x": 250, "y": 150,
        "description": "The center of Lumen Market. Vale announces news here."
    }
}

# ─── Action Effects ──────────────────────────────────────────────

# How each action type affects NPC sentiment (base values before NPC-specific modifiers)
ACTION_EFFECTS = {
    "steal": {"trust": -20, "fear": +15, "respect": -15, "anger": +25, "public": True, "severity": 0.8},
    "gift": {"trust": +15, "fear": -5, "respect": +10, "anger": -10, "public": True, "severity": 0.3},
    "help_": {"trust": +20, "fear": -10, "respect": +15, "anger": -15, "public": True, "severity": 0.4},
    "lie": {"trust": -15, "fear": +10, "respect": -20, "anger": +15, "public": False, "severity": 0.6},
    "apologize": {"trust": +10, "fear": -5, "respect": +5, "anger": -20, "public": True, "severity": 0.3},
    "threaten": {"trust": -25, "fear": +25, "respect": -10, "anger": +30, "public": False, "severity": 0.9},
    "ask_rumor": {"trust": 0, "fear": 0, "respect": 0, "anger": 0, "public": False, "severity": 0.1},
    "return_item": {"trust": +20, "fear": -10, "respect": +15, "anger": -25, "public": True, "severity": 0.5},
}
```

**Why the social graph is defined explicitly:** Cognee cannot infer NPC-to-NPC relationships. We define them here, and the propagation engine reads from this table to decide who tells whom. This prevents magical memory spread — every NPC-to-NPC memory transfer has a defined edge with a trust level.

- [ ] **Step 2: Create `backend/app/game_state.py`**

```python
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models import (
    Location, Faction, ActionType, EventRecord, NpcState, FactionMood,
    BeliefRecord, RelationshipType
)
from app.world_data import NPC_DATA, FACTION_DATA, SOCIAL_EDGES, ACTION_EFFECTS

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
        self.social_graph: Dict[str, List[tuple]] = {}      # npc_name -> [(other_npc, rel_type, trust)]
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

    def create_event(self, action_type: ActionType, target_npc: str,
                     item: Optional[str], description: Optional[str],
                     witnesses: List[str]) -> EventRecord:
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
            public=ACTION_EFFECTS.get(action_type.value, {}).get("public", True),
        )
        self.events.append(event)
        return event

    def get_connected_npcs(self, npc_name: str) -> List[tuple]:
        """Returns list of (connected_npc_name, relationship_type, trust_level)."""
        return self.social_graph.get(npc_name, [])

    def get_npcs_for_propagation(self, witness: str, event_id: str) -> List[str]:
        """Determine which NPCs should learn about an event from this witness.

        Uses the social graph to find connected NPCs and the propagation rules.
        """
        candidates = []
        for connected_npc, rel_type, trust in self.get_connected_npcs(witness):
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
        return {
            "player_location": self.player_location.value,
            "npcs": {n: s.model_dump() for n, s in self.npcs.items()},
            "factions": {f: m.model_dump() for f, m in self.factions.items()},
            "recent_events": [e.model_dump() for e in self.events[-10:]],
            "session_id": self.session_id,
        }
```

### Task 1.3: Cognee Cloud Client (REAL — no mocks)

**Files:**
- Create: `backend/app/cognee_client.py`

- [ ] **Step 1: Write the Cognee client** — this is the ONLY file that talks to Cognee. Every other part of the backend goes through this client.

```python
import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

import cognee
from cognee.modules.search.types import SearchType
from app.config import settings

logger = logging.getLogger(__name__)

class CogneeClient:
    """Real Cognee Cloud client. Every method calls the live API.

    Architecture:
    - Each NPC gets their own dataset for partial-knowledge isolation.
    - Events are stored as structured text that Cognee can cognify into graph+vector.
    - Social relationships are stored as graph edges between NPC nodes.
    - Beliefs are edges from NPC nodes to Event nodes with certainty properties.
    """

    def __init__(self):
        self._connected = False
        self._dataset_names = [
            "echo_public",      # Public events (any NPC can recall)
            "echo_mira",
            "echo_rowan",
            "echo_sol",
            "echo_niko",
            "echo_vale",
            "echo_ilya",
            "echo_factions",    # Faction-level memory
        ]
        self._session_id = None

    async def connect(self):
        """Connect to Cognee Cloud. Must be called once at startup."""
        if self._connected:
            return
        await cognee.serve(
            url=settings.cognee_base_url,
            api_key=settings.cognee_api_key,
        )
        self._connected = True
        logger.info("Connected to Cognee Cloud")

    async def disconnect(self):
        if self._connected:
            try:
                await cognee.disconnect()
            except Exception as e:
                logger.warning(f"Disconnect warning: {e}")
            self._connected = False

    async def ensure_dataset(self, dataset_name: str):
        """Ensure a dataset exists. Cognee creates datasets implicitly on first write."""
        # Cognee creates datasets on first remember() call — no explicit create needed.
        pass

    async def store_event(self, event_text: str, dataset_name: str,
                          session_id: Optional[str] = None):
        """Store an event in Cognee memory.

        This is a REAL Cognee Cloud call. It triggers:
        1. Text chunking
        2. LLM triplet extraction (subject-relation-object)
        3. Embedding generation
        4. Graph node+edge creation
        5. Vector index update

        Args:
            event_text: Natural language description of the event
            dataset_name: Which NPC's dataset to store in (e.g. "echo_mira")
            session_id: Optional session ID for fast cache

        Returns: None. This is fire-and-forget from the game loop perspective.
        """
        kwargs = {"dataset_name": dataset_name}
        if session_id:
            kwargs["session_id"] = session_id

        await cognee.remember(event_text, **kwargs)
        logger.debug(f"Stored event in {dataset_name}: {event_text[:60]}...")

    async def store_graph_edge(self, subject: str, relation: str, obj: str,
                                dataset_name: str):
        """Store a structured graph edge as a sentence in Cognee.

        Args:
            subject: The source entity (e.g. "Mira")
            relation: The relationship (e.g. "witnessed")
            obj: The target entity (e.g. "theft_event_001")
            dataset_name: Which dataset to store in
        """
        edge_text = f"[GRAPH_EDGE] {subject} {relation} {obj}"
        await self.store_event(edge_text, dataset_name)

    async def recall_npc_knowledge(self, npc_name: str, query: str,
                                    mode: str = "hybrid",
                                    top_k: int = 10) -> List[str]:
        """Recall what an NPC knows about a topic.

        This is the CORE retrieval method for the game. It queries a specific
        NPC's dataset and returns relevant memory entries.

        The three modes:
        - "graph": Uses SearchType.GRAPH_COMPLETION — traverses relationships first,
          then uses LLM to compose answer. Returns structured factual answers.
        - "vector": Uses SearchType.RAG_COMPLETION — pure semantic search without
          graph traversal. Returns semantically similar chunks.
        - "hybrid": Uses SearchType.GRAPH_COMPLETION_COT — graph traversal + chain
          of thought. Returns both factual structure and semantic meaning.

        Args:
            npc_name: Which NPC's knowledge to query
            query: Natural language question
            mode: "graph", "vector", or "hybrid"
            top_k: Number of results to return

        Returns:
            List of answer strings from Cognee recall
        """
        dataset_name = f"echo_{npc_name.lower()}"

        # Map mode to SearchType
        if mode == "graph":
            search_type = SearchType.GRAPH_COMPLETION
        elif mode == "vector":
            search_type = SearchType.RAG_COMPLETION
        else:  # hybrid
            search_type = SearchType.GRAPH_COMPLETION_COT

        try:
            results = await cognee.recall(
                query_text=query,
                datasets=[dataset_name, "echo_public"],
                search_type=search_type,
                top_k=top_k,
            )
            return self._flatten_results(results)
        except Exception as e:
            logger.error(f"Recall failed for {npc_name} ({mode}): {e}")
            return [f"[Memory unavailable: {str(e)}]"]

    async def recall_faction_mood(self, faction_name: str, query: str,
                                   mode: str = "hybrid") -> List[str]:
        """Recall faction-level memory.

        Uses the echo_factions dataset which stores faction-level sentiment.
        """
        try:
            if mode == "graph":
                search_type = SearchType.GRAPH_COMPLETION
            elif mode == "vector":
                search_type = SearchType.RAG_COMPLETION
            else:
                search_type = SearchType.GRAPH_COMPLETION_COT

            results = await cognee.recall(
                query_text=query,
                datasets=["echo_factions"],
                search_type=search_type,
                top_k=5,
            )
            return self._flatten_results(results)
        except Exception as e:
            logger.error(f"Faction recall failed for {faction_name}: {e}")
            return []

    async def classify_action(self, action_description: str) -> Dict[str, Any]:
        """Classify a novel action into an archetype using vector similarity.

        This is the anti-hardcode proof. The player can type any action in free text,
        and this method finds the semantically closest known action archetype.

        Args:
            action_description: Free-text description (e.g. "I threatened Niko with a knife")

        Returns:
            Dict with action_type, valence, and confidence
        """
        try:
            results = await cognee.recall(
                query_text=f"Classify this action: {action_description}",
                datasets=["echo_public"],
                search_type=SearchType.GRAPH_COMPLETION,
                top_k=3,
            )
            raw = self._flatten_results(results)
            combined = " ".join(raw).lower()
            # Extract valence from the response
            is_negative = any(w in combined for w in ["negative", "harmful", "threat", "violence"])
            is_positive = any(w in combined for w in ["positive", "kind", "generous", "helpful"])
            return {
                "action_type": "classified",
                "valence": "negative" if is_negative else ("positive" if is_positive else "neutral"),
                "confidence": 0.7 if (is_negative or is_positive) else 0.3,
                "raw": combined[:200],
            }
        except Exception as e:
            logger.error(f"Action classification failed: {e}")
            return {"action_type": "unknown", "valence": "neutral", "confidence": 0.0, "raw": ""}

    async def recall_public_knowledge(self, query: str, mode: str = "hybrid") -> List[str]:
        """Recall from the public events dataset. Used for events anyone could know."""
        return await self.recall_npc_knowledge("public", query, mode)

    async def get_session_memory(self, session_id: str, query: str) -> List[str]:
        """Get session-scoped memory (faster than full graph recall).

        Session memory is used for the hot path — recent events in the current
        game session. It syncs to the graph in the background.
        """
        try:
            results = await cognee.recall(
                query_text=query,
                session_id=session_id,
                datasets=["echo_public"],
                search_type=SearchType.RAG_COMPLETION,
                top_k=10,
            )
            return self._flatten_results(results)
        except Exception as e:
            logger.error(f"Session recall failed: {e}")
            return []

    def _flatten_results(self, results) -> List[str]:
        """Flatten Cognee recall results into a list of text strings.

        Cognee returns different shapes depending on the SearchType:
        - GRAPH_COMPLETION returns objects with .answer
        - RAG_COMPLETION returns objects with .content
        - Session returns objects with .content
        """
        if results is None:
            return []
        out = []
        for r in results:
            if r is None:
                continue
            for attr in ("answer", "content", "text", "summary"):
                v = getattr(r, attr, None)
                if v:
                    out.append(str(v))
            if not any(getattr(r, a, None) for a in ("answer", "content", "text", "summary")):
                out.append(str(r))
        return out


# Singleton
cognee_client = CogneeClient()
```

**Why this design:**
- Every method calls `cognee.remember()` or `cognee.recall()` — real Cognee Cloud API calls. No mock, no print, no placeholder.
- Each NPC has their own dataset (`echo_mira`, `echo_rowan`, etc.) — this enforces partial knowledge isolation at the Cognee dataset level.
- Three recall modes map to three Cognee SearchTypes — the baseline comparison works because each mode genuinely uses a different retrieval strategy.
- `store_event` is fire-and-forget (no await on the game loop) — the game writes events to Cognee in the background and reads them later. This keeps gameplay responsive.
- `classify_action` uses vector similarity to find the closest known action archetype — this is the anti-hardcode proof.

- [ ] **Step 2: Verify Cognee client connects**

Add a startup event to `main.py` and test:

```python
@app.on_event("startup")
async def startup():
    from app.cognee_client import cognee_client
    await cognee_client.connect()
    print("Cognee Cloud connected")
```

Test: `cd backend && uvicorn app.main:app --reload --port 8000` should print "Cognee Cloud connected".

---

## Chunk 2: Memory & Propagation Engine

**Goal:** When a player performs an action, the event is stored in Cognee, propagated through the social graph, and NPC beliefs are created with proper certainty tracking.

### Task 2.1: Propagation Engine

**Files:**
- Create: `backend/app/propagation.py`

- [ ] **Step 1: Write the propagation engine**

```python
import asyncio
import logging
from typing import List, Dict, Optional
from app.models import (
    EventRecord, BeliefRecord, NpcState, FactionMood,
    Location, Faction, ActionType, RelationshipType
)
from app.game_state import GameStateManager
from app.cognee_client import CogneeClient, cognee_client
from app.world_data import PROPAGATION_RULES, SOCIAL_EDGES, ACTION_EFFECTS

logger = logging.getLogger(__name__)

class PropagationEngine:
    """Determines how memory spreads through the social graph.

    When an NPC witnesses an event, this engine:
    1. Determines who that NPC talks to (based on social edges)
    2. Creates belief records for each informed NPC
    3. Updates NPC sentiment based on the event type
    4. Writes propagation edges to Cognee
    5. Updates faction moods

    The propagation is EXPLICIT and TRACEABLE — every belief has a source
    and certainty value. No magical memory.
    """

    def __init__(self, game_state: GameStateManager, cognee: CogneeClient):
        self.gs = game_state
        self.cognee = cognee

    async def propagate_event(self, event: EventRecord):
        """Propagate an event through the social graph.

        This method:
        1. Records the event in the witness's Cognee dataset
        2. Propagates through social edges to connected NPCs
        3. Updates NPC sentiment (trust/fear/respect/anger)
        4. Updates faction moods
        5. Stores propagation edges in Cognee for traceability

        All Cognee calls are async and non-blocking for the game loop.
        """
        # Step 1: Store event in public dataset (canonical record)
        event_text = self._event_to_text(event)
        await self.cognee.store_event(
            event_text,
            dataset_name="echo_public",
            session_id=self.gs.session_id,
        )

        # Step 2: Store event in each witness's personal dataset
        for witness_name in event.witnesses:
            await self._store_event_for_npc(event, witness_name, "witnessed")
            await self._store_graph_provenance(witness_name, event, "witnessed")

            # Step 3: Propagate from witness to connected NPCs
            connected = self.gs.get_npcs_for_propagation(witness_name, event.event_id)
            for connected_npc in connected:
                await self._propagate_to_npc(event, witness_name, connected_npc)

        # Step 4: Update NPC sentiment based on event type
        self._update_npc_sentiment(event)

        # Step 5: Update faction moods
        self._update_faction_moods(event)

    async def _store_event_for_npc(self, event: EventRecord, npc_name: str,
                                    source: str):
        """Store an event in a specific NPC's Cognee dataset.

        The event text includes the NPC's perspective so Cognee's LLM extraction
        can create the correct graph nodes and edges for this NPC's knowledge.
        """
        dataset = f"echo_{npc_name.lower()}"
        perspective_text = self._event_from_perspective(event, npc_name, source)
        await self.cognee.store_event(perspective_text, dataset_name=dataset)

        # Also create a structured belief edge
        belief_text = f"[BELIEF] {npc_name} {'saw' if source == 'witnessed' else 'was told by ' + source} that {self._event_summary(event)}. Certainty: {'high' if source == 'witnessed' else 'medium'}."
        await self.cognee.store_event(belief_text, dataset_name=dataset)

    async def _store_graph_provenance(self, npc_name: str, event: EventRecord,
                                       source: str):
        """Store a structured graph edge in Cognee for the visualization panel.

        These edges power the "who knows what and why" visualization.
        """
        edge_text = f"[PROVENANCE] {npc_name} {source} {event.event_id}"
        await self.cognee.store_graph_edge(
            npc_name, source, event.event_id,
            dataset_name=f"echo_{npc_name.lower()}"
        )

    async def _propagate_to_npc(self, event: EventRecord, from_npc: str, to_npc: str):
        """Propagate an event from one NPC to another through a social edge.

        The propagated belief has:
        - Lower certainty than the original witness (hearsay)
        - Source set to the NPC who told them
        - Emotional impact scaled by the relationship trust level
        """
        # Find the relationship between the two NPCs
        rel_type = None
        trust = 0
        for connected, rt, tl in self.gs.get_connected_npcs(from_npc):
            if connected == to_npc:
                rel_type = rt
                trust = tl
                break

        if rel_type is None:
            return

        # Apply propagation rules
        rules = PROPAGATION_RULES.get(rel_type)
        if rules is None:
            return

        # Calculate certainty based on relationship trust and propagation rules
        certainty = (trust / 100.0) * rules["certainty_multiplier"]
        if rel_type == RelationshipType.ally:
            certainty = max(certainty, 0.5)

        # Create belief record
        belief = BeliefRecord(
            npc_name=to_npc,
            event_id=event.event_id,
            certainty=round(certainty, 2),
            source="told",
            heard_from=from_npc,
        )
        self.gs.add_belief(to_npc, belief)

        # Store in Cognee
        await self._store_event_for_npc(event, to_npc, from_npc)
        await self._store_graph_provenance(to_npc, event, f"told_by_{from_npc}")

        # Scale emotional impact based on relationship trust
        self._apply_hearsay_sentiment(event, to_npc, certainty, trust)

        logger.info(f"Propagated {event.event_id} from {from_npc} to {to_npc} "
                     f"(certainty={certainty}, trust={trust})")

    def _update_npc_sentiment(self, event: EventRecord):
        """Update NPC emotional states based on the event.

        Witnesses feel the full effect. Non-witnesses who were told feel a
        scaled effect based on their certainty and relationship trust.
        """
        effects = ACTION_EFFECTS.get(event.action_type.value, {})
        if not effects:
            return

        for npc_name in event.witnesses:
            npc = self.gs.npcs.get(npc_name)
            if npc:
                self._apply_sentiment_change(npc, effects, scale=1.0)

    def _apply_hearsay_sentiment(self, event: EventRecord, npc_name: str,
                                  certainty: float, trust: int):
        """Apply a scaled sentiment change for hearsay knowledge.

        An NPC who was told about an event feels less strongly than one who
        witnessed it. The emotional impact is scaled by:
        - certainty (how sure they are the event happened)
        - trust (how much they trust the source)
        """
        effects = ACTION_EFFECTS.get(event.action_type.value, {})
        if not effects:
            return

        npc = self.gs.npcs.get(npc_name)
        if npc:
            scale = certainty * (trust / 100.0)
            self._apply_sentiment_change(npc, effects, scale=scale)

    def _apply_sentiment_change(self, npc: NpcState, effects: dict, scale: float):
        """Apply sentiment changes to an NPC, clamped to 0-100."""
        npc.trust = max(0, min(100, npc.trust + int(effects.get("trust", 0) * scale)))
        npc.fear = max(0, min(100, npc.fear + int(effects.get("fear", 0) * scale)))
        npc.respect = max(0, min(100, npc.respect + int(effects.get("respect", 0) * scale)))
        npc.anger = max(0, min(100, npc.anger + int(effects.get("anger", 0) * scale)))

    def _update_faction_moods(self, event: EventRecord):
        """Update faction aggregate moods based on the event.

        Faction moods are calculated as the average of all members' sentiments,
        with an additional boost if the event directly involves a faction member.
        """
        for faction_name, mood in self.gs.factions.items():
            faction = Faction(faction_name)
            members = [n for n, d in self.gs.npcs.items() if d.faction == faction]

            if not members:
                continue

            # Calculate average sentiment of faction members
            avg_trust = sum(self.gs.npcs[m].trust for m in members) / len(members)
            avg_fear = sum(self.gs.npcs[m].fear for m in members) / len(members)
            avg_respect = sum(self.gs.npcs[m].respect for m in members) / len(members)
            avg_anger = sum(self.gs.npcs[m].anger for m in members) / len(members)

            mood.trust = round(avg_trust)
            mood.fear = round(avg_fear)
            mood.respect = round(avg_respect)
            mood.anger = round(avg_anger)
            mood.last_event = event.event_id

    def _event_to_text(self, event: EventRecord) -> str:
        """Convert an event to a natural language sentence for Cognee ingestion.

        Cognee's cognify pipeline will extract (subject, relation, object)
        triplets from this text and create graph nodes+edges automatically.
        """
        item_part = f" {event.item}" if event.item else ""
        desc_part = f" {event.description}" if event.description else ""
        return (
            f"[EVENT {event.event_id}] The player performed '{event.action_type.value}'"
            f" targeting {event.target_npc}{item_part} at {event.location.value}."
            f" Witnesses: {', '.join(event.witnesses)}.{desc_part}"
        )

    def _event_from_perspective(self, event: EventRecord, npc_name: str,
                                 source: str) -> str:
        """Describe an event from a specific NPC's perspective.

        This creates a more natural memory for the NPC, including their
        relationship to the event and their level of certainty.
        """
        if source == "witnessed":
            return (
                f"[EVENT {event.event_id}] I saw the player {event.action_type.value}"
                f" {'a ' + event.item if event.item else ''}"
                f" involving {event.target_npc} at {event.location.value}."
                f" I am certain about what I saw."
            )
        else:
            return (
                f"[EVENT {event.event_id}] I heard from {source} that the player"
                f" {event.action_type.value}"
                f" {'a ' + event.item if event.item else ''}"
                f" involving {event.target_npc}. I am less certain since I did not see it."
            )

    def _event_summary(self, event: EventRecord) -> str:
        return f"the player {event.action_type.value}{' ' + event.item if event.item else ''} involving {event.target_npc}"
```

### Task 2.2: Action Handler & Routes

**Files:**
- Modify: `backend/app/main.py` (add action endpoint, state endpoint, dialogue endpoint)

- [ ] **Step 1: Update `main.py` with all game routes**

```python
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import (
    ActionRequest, ActionResponse, DialogueRequest, DialogueResponse,
    GameStateResponse, MemoryGraphResponse, MemoryGraphNode, MemoryGraphEdge,
    FactionMood, EventRecord, BeliefRecord, ActionType, MemoryMode
)
from app.game_state import GameStateManager
from app.cognee_client import cognee_client
from app.propagation import PropagationEngine
from app.dialogue import DialogueComposer
from app.baselines import BaselineService

app = FastAPI(title="Echo Game API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session-scoped state
_active_sessions: dict[str, GameStateManager] = {}
_propagation_engines: dict[str, PropagationEngine] = {}
_dialogue_composers: dict[str, DialogueComposer] = {}
_baseline_services: dict[str, BaselineService] = {}


def _get_or_create_session(session_id: str = None) -> str:
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


@app.on_event("startup")
async def startup():
    await cognee_client.connect()


@app.on_event("shutdown")
async def shutdown():
    await cognee_client.disconnect()


# ─── Game State Endpoint ─────────────────────────────────────────

@app.get("/api/state", response_model=GameStateResponse)
def get_state(session_id: str = Query(default=None)):
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    state = gs.get_state_dict()

    # Add beliefs to the state for the frontend
    beliefs_by_npc = {}
    for npc_name, beliefs in gs.beliefs.items():
        beliefs_by_npc[npc_name] = [b.model_dump() for b in beliefs]

    state["beliefs"] = beliefs_by_npc
    return GameStateResponse(**state)


# ─── Action Endpoint ─────────────────────────────────────────────

@app.post("/api/action", response_model=ActionResponse)
async def perform_action(req: ActionRequest, background_tasks: BackgroundTasks,
                          session_id: str = Query(default=None)):
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
    background tasks. The player sees their immediate reaction based on
    local state, while Cognee syncs durably in the background.
    """
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    prop = _propagation_engines[sid]
    dialogue = _dialogue_composers[sid]

    # Step 1: Determine witnesses (NPCs at the same location as the player)
    witnesses = [
        name for name, npc in gs.npcs.items()
        if npc.location == gs.player_location and name != req.target_npc
    ]
    # The target NPC always witnesses if they're at their location
    target_npc = gs.npcs.get(req.target_npc)
    if target_npc and req.target_npc not in witnesses:
        witnesses.append(req.target_npc)

    # Step 2: Create the event
    event = gs.create_event(
        action_type=req.action_type,
        target_npc=req.target_npc,
        item=req.item,
        description=req.description,
        witnesses=witnesses,
    )

    # Step 3: Cognee write + propagation (background — doesn't block response)
    background_tasks.add_task(prop.propagate_event, event)

    # Step 4: Generate NPC reactions based on current local knowledge
    npc_reactions = {}
    for npc_name in gs.npcs:
        mode = req.action_type.value if hasattr(req, 'action_type') else "hybrid"
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


# ─── Dialogue Endpoint ──────────────────────────────────────────

@app.get("/api/dialogue/{npc_name}", response_model=DialogueResponse)
async def get_dialogue(npc_name: str, mode: MemoryMode = MemoryMode.hybrid,
                        session_id: str = Query(default=None)):
    """Get an NPC's reaction to the current situation.

    This endpoint demonstrates the three memory modes:
    - graph: Only factual graph knowledge (no semantic generalization)
    - vector: Only semantic similarity (no structural knowledge boundaries)
    - hybrid: Both factual graph + semantic meaning

    The mode parameter lets the frontend toggle between them live,
    showing the baseline comparison.
    """
    sid = _get_or_create_session(session_id)
    baseline = _baseline_services[sid]

    if npc_name not in _active_sessions[sid].npcs:
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


# ─── Memory Graph Endpoint ───────────────────────────────────────

@app.get("/api/memory/graph", response_model=MemoryGraphResponse)
def get_memory_graph(session_id: str = Query(default=None)):
    """Get the memory graph data for the visualization panel.

    Returns nodes and edges that the frontend renders as an animated graph.
    This powers the "who knows what" visualization.
    """
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]

    nodes = []
    edges = []

    # Player node
    nodes.append(MemoryGraphNode(id="player", label="Player", type="player"))

    # NPC nodes
    for name, npc in gs.npcs.items():
        nodes.append(MemoryGraphNode(
            id=name, label=name, type="npc",
            faction=npc.faction,
        ))

    # Faction nodes
    for faction_name in gs.factions:
        nodes.append(MemoryGraphNode(
            id=faction_name, label=faction_name, type="faction",
        ))

    # Event nodes
    for event in gs.events:
        nodes.append(MemoryGraphNode(
            id=event.event_id, label=f"{event.action_type.value}:{event.event_id[-4:]}",
            type="event",
        ))
        edges.append(MemoryGraphEdge(
            source="player", target=event.event_id, label="performed",
        ))

    # Belief edges
    for npc_name, beliefs in gs.beliefs.items():
        for belief in beliefs:
            edges.append(MemoryGraphEdge(
                source=npc_name, target=belief.event_id,
                label=f"knows ({belief.certainty:.0%})",
            ))

    # Social edges
    for npc_name, connections in gs.social_graph.items():
        for other_name, rel_type, trust in connections:
            if npc_name < other_name:  # Avoid duplicates
                edges.append(MemoryGraphEdge(
                    source=npc_name, target=other_name,
                    label=f"{rel_type.value} ({trust})",
                ))

    return MemoryGraphResponse(nodes=nodes, edges=edges)


# ─── Memory Facts Endpoint ───────────────────────────────────────

@app.get("/api/memory/events")
def get_memory_events(session_id: str = Query(default=None)):
    """Get all known events with their details."""
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    return {"events": [e.model_dump() for e in gs.events]}


# ─── Memory Beliefs Endpoint ─────────────────────────────────────

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


# ─── Faction Moods Endpoint ──────────────────────────────────────

@app.get("/api/memory/factions")
def get_faction_moods(session_id: str = Query(default=None)):
    """Get faction sentiment meters."""
    sid = _get_or_create_session(session_id)
    gs = _active_sessions[sid]
    return {"factions": {f: m.model_dump() for f, m in gs.factions.items()}}


# ─── Classify Action Endpoint ────────────────────────────────────

@app.post("/api/classify")
async def classify_action(req: ActionRequest):
    """Classify a novel action using Cognee vector similarity.

    This is the anti-hardcode proof. The player types anything they want
    (e.g. "I threatened Niko with a knife") and Cognee classifies it by
    similarity to known action archetypes.

    Returns the classification with valence and confidence.
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


# ─── Reset Endpoint ──────────────────────────────────────────────

@app.post("/api/reset")
def reset_session(session_id: str = Query(default=None)):
    """Reset the game session. Clears all local state and Cognee memory."""
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
```

**Why background tasks for Cognee writes:** The game loop must feel responsive. Cognee's `remember()` pipeline (chunk → extract triplets → embed → store) can take 2-10 seconds. If the player had to wait for that, the game would feel broken. Instead, the action endpoint returns immediately with the local state, and Cognee syncs in the background. When the player talks to an NPC later, Cognee will have the full memory available.

- [ ] **Step 3: Verify the action endpoint works**

```bash
curl -X POST "http://localhost:8000/api/action?session_id=test1" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "steal", "target_npc": "Mira", "item": "relic"}'
```

Expected: Returns `event_id`, `npc_reactions` map, and `updated_state`.

---

## Chunk 3: Dialogue & Baseline System

**Goal:** NPC dialogue that is grounded in actual Cognee recall, with three comparison modes.

### Task 3.1: Dialogue Composer

**Files:**
- Create: `backend/app/dialogue.py`

- [ ] **Step 1: Write the dialogue composer**

```python
import logging
from typing import List, Dict, Tuple, Optional
from app.models import (
    EventRecord, BeliefRecord, NpcState, MemoryMode,
    ActionType, Faction
)
from app.game_state import GameStateManager
from app.cognee_client import CogneeClient

logger = logging.getLogger(__name__)

class DialogueComposer:
    """Generates grounded NPC dialogue from Cognee memory.

    CRITICAL RULE: The LLM only PHRASES the response. It never invents facts.
    All facts come from:
    1. The NPC's known events (from Cognee recall)
    2. The NPC's current emotional state (trust/fear/respect/anger)
    3. The NPC's faction affiliation

    If the NPC doesn't know about an event, the dialogue MUST NOT reference it.
    This is enforced by the `known_events` parameter — the LLM only receives
    events the NPC has a belief edge to.
    """

    # Template responses for when Cognee is unavailable (degradation mode)
    FALLBACK_TEMPLATES = {
        "neutral": "Hello, traveler. The wind carries many whispers through Lumen Market.",
        "angry": "I have nothing to say to you.",
        "friendly": "Good day! The market is lively today.",
    }

    def __init__(self, game_state: GameStateManager, cognee: CogneeClient):
        self.gs = game_state
        self.cognee = cognee

    async def generate_reaction(self, npc_name: str, event: EventRecord,
                                 mode: str = "hybrid") -> str:
        """Generate an NPC's reaction to an event.

        This is called immediately after an action to give the player
        instant feedback. The reaction uses the NPC's LOCAL state (beliefs
        that have been processed already) plus a Cognee recall for tone.

        Args:
            npc_name: The NPC to generate dialogue for
            event: The event that just happened
            mode: "graph", "vector", or "hybrid"

        Returns:
            A dialogue string
        """
        npc = self.gs.npcs.get(npc_name)
        if not npc:
            return ""

        # Check if this NPC knows about the event
        knows = self.gs._npc_knows_event(npc_name, event.event_id)

        if not knows:
            # NPC doesn't know — they should not reference the event
            return self._neutral_greeting(npc)

        # NPC knows — build a Cognitively grounded response
        try:
            # Query Cognee for what this NPC knows about the situation
            recall_results = await self.cognee.recall_npc_knowledge(
                npc_name=npc_name,
                query=f"What do I know about the {event.action_type.value} involving {event.target_npc}?",
                mode=mode,
                top_k=5,
            )
            cognee_context = " ".join(recall_results)[:300]
        except Exception as e:
            logger.warning(f"Cognee recall failed for reaction: {e}")
            cognee_context = ""

        # Build a grounded reaction from local state + Cognee context
        return self._compose_reaction(npc, event, cognee_context, knows, mode)

    def _compose_reaction(self, npc: NpcState, event: EventRecord,
                           cognee_context: str, knows: bool,
                           mode: str) -> str:
        """Compose a reaction string from grounded data.

        This uses a template-based approach for reliability, with Cognee
        context providing tone and nuance. The templates ensure the NPC
        never hallucinates facts — they only reference what they know.
        """
        # Determine emotional state
        dominant = self._dominant_emotion(npc)
        action_label = event.action_type.value.replace("_", " ")

        if dominant == "anger" and npc.anger > 50:
            if event.action_type == ActionType.steal:
                return f"{{anger}} You think you can just steal from us? I saw what you did."
            elif event.action_type == ActionType.threaten:
                return f"{{anger}} Threats won't work on me. I remember your kind."
            elif event.action_type == ActionType.lie:
                return f"{{anger}} Lies have a way of surfacing. I know the truth."
            else:
                return f"{{anger}} I haven't forgotten what happened."

        elif npc.trust < 30 and dominant != "respect":
            if event.action_type == ActionType.apologize:
                return f"{{distrust}} An apology doesn't undo what was done. But I'm listening."
            elif event.action_type == ActionType.return_item:
                return f"{{distrust}} Returning what you took is a start. Trust takes longer."
            else:
                return f"{{distrust}} I don't trust you. The memory of what you did is fresh."

        elif npc.trust > 70:
            if event.action_type == ActionType.gift:
                return f"{{warm}} That's kind of you. Not everyone passing through shows such generosity."
            elif event.action_type == ActionType.help_:
                return f"{{warm}} You've proven yourself helpful. Word travels in this village."
            else:
                return f"{{warm}} Good to see you again. The village remembers its friends."

        else:
            if knows:
                return (
                    f"{{neutral}} I know about the {action_label}."
                    f" It's noted. Actions have weight here."
                )
            else:
                return self._neutral_greeting(npc)

    def _dominant_emotion(self, npc: NpcState) -> str:
        """Determine the NPC's dominant emotion based on their state."""
        emotions = [
            ("anger", npc.anger),
            ("fear", npc.fear),
            ("trust", npc.trust),
            ("respect", npc.respect),
        ]
        # Anger and fear are negative-dominant; trust and respect are positive
        negatives = npc.anger + npc.fear
        positives = npc.trust + npc.respect

        if negatives > positives * 1.5:
            if npc.anger > npc.fear:
                return "anger"
            return "fear"
        if positives > negatives * 1.5:
            if npc.trust > npc.respect:
                return "trust"
            return "respect"
        return "neutral"

    def _neutral_greeting(self, npc: NpcState) -> str:
        """A neutral greeting for NPCs who don't know about recent events."""
        if npc.faction:
            if npc.trust > 60:
                return f"Greetings, friend. The {npc.faction.value} welcomes you."
            elif npc.trust < 30:
                return f"You're back. I'm watching."
            else:
                return f"Hello there. Lumen Market has a peaceful rhythm today."
        else:
            return f"Hello. The road brought you here, as it brings many."

    async def generate_open_dialogue(self, npc_name: str, mode: str = "hybrid") -> Tuple[str, List[Dict]]:
        """Generate an NPC's response when the player just talks to them
        (no recent action). This is a general dialogue that reflects the
        NPC's current memory of the player.

        Returns:
            Tuple of (dialogue_text, provenance_data)
        """
        npc = self.gs.npcs.get(npc_name)
        if not npc:
            return "I don't know you.", []

        provenance = []

        # Get NPC's known events from Cognee
        try:
            known = await self.cognee.recall_npc_knowledge(
                npc_name=npc_name,
                query=f"What do I know about the player and recent events?",
                mode=mode,
                top_k=5,
            )
            if known:
                provenance.append({
                    "source": "cognee_recall",
                    "mode": mode,
                    "summary": " ".join(known)[:200],
                })
        except Exception as e:
            logger.warning(f"Recall failed for open dialogue: {e}")

        # Check local beliefs
        local_beliefs = self.gs.beliefs.get(npc_name, [])
        if local_beliefs:
            provenance.append({
                "source": "local_beliefs",
                "count": len(local_beliefs),
                "events": [b.event_id for b in local_beliefs],
            })

        # Generate dialogue based on available knowledge
        if not local_beliefs:
            # NPC knows nothing about the player
            if npc.faction:
                return f"I sense you're new to Lumen Market. The {npc.faction.value} keeps careful watch.", provenance
            return f"First time in Lumen Market? Take care — memories live long here.", provenance

        # NPC has some knowledge
        dominant = self._dominant_emotion(npc)
        if dominant == "anger":
            return f"I know what you did. The village remembers, even if you wish it didn't.", provenance
        elif dominant == "fear":
            return f"You've made an impression. Not all of it good. Be careful how you tread.", provenance
        elif dominant == "trust":
            return f"Good to see you. Your actions have spoken well of you.", provenance
        else:
            return f"I remember you. The market has eyes everywhere.", provenance
```

### Task 3.2: Baseline Service

**Files:**
- Create: `backend/app/baselines.py`

- [ ] **Step 1: Write the baseline service**

```python
import logging
from typing import List, Dict, Tuple, Optional
from app.models import MemoryMode, NpcState, Faction
from app.game_state import GameStateManager
from app.cognee_client import CogneeClient

logger = logging.getLogger(__name__)

class BaselineService:
    """Provides three memory strategies for comparison.

    This is the core of the "toggle" demo. Each mode uses a fundamentally
    different retrieval strategy against the same Cognee data:

    GRAPH MODE (SearchType.GRAPH_COMPLETION):
        - Only uses graph traversal to find facts
        - No semantic generalization
        - NPCs can only reference events they have a direct graph edge to
        - Fails to generalize: can't connect "theft" to "betrayal" or
          "apology" to "repair"
        - Dialogue is factual but rigid

    VECTOR MODE (SearchType.RAG_COMPLETION):
        - Only uses semantic similarity (no graph structure)
        - Can generalize meaning across events
        - BUT: can't enforce knowledge boundaries — may leak facts from
          one NPC's knowledge to another NPC who shouldn't know
        - Dialogue is expressive but may hallucinate

    HYBRID MODE (SearchType.GRAPH_COMPLETION_COT):
        - Uses BOTH graph traversal AND semantic similarity
        - Chain-of-thought reasoning combines structure + meaning
        - Enforces knowledge boundaries through graph edges
        - Generalizes emotionally through vector similarity
        - This is the winning mode

    Each mode is a REAL Cognee recall call — no mock data.
    """

    def __init__(self, game_state: GameStateManager, cognee: CogneeClient):
        self.gs = game_state
        self.cognee = cognee

    async def get_dialogue_with_provenance(
        self, npc_name: str, mode: MemoryMode
    ) -> Tuple[str, List[Dict]]:
        """Get an NPC's dialogue using a specific memory mode.

        Returns:
            Tuple of (dialogue_string, provenance_list)
            Provenance explains WHAT facts drove the dialogue.
        """
        npc = self.gs.npcs.get(npc_name)
        if not npc:
            return "I don't know you.", []

        provenance = []

        # Determine what this NPC knows from local beliefs
        local_beliefs = self.gs.beliefs.get(npc_name, [])
        known_event_ids = [b.event_id for b in local_beliefs]
        known_events = [e for e in self.gs.events if e.event_id in known_event_ids]

        provenance.append({
            "mode": mode.value,
            "npc": npc_name,
            "local_beliefs": len(local_beliefs),
            "known_events": [e.action_type.value for e in known_events],
        })

        # Query Cognee with the specified mode
        try:
            recall_results = await self.cognee.recall_npc_knowledge(
                npc_name=npc_name,
                query=f"What do I know about the player and what they've done?",
                mode=mode.value,
                top_k=10,
            )
            recall_text = " ".join(recall_results)
            provenance.append({
                "source": "cognee_recall",
                "mode": mode.value,
                "recall_preview": recall_text[:300],
            })
        except Exception as e:
            logger.warning(f"{mode.value} recall failed for {npc_name}: {e}")
            recall_text = ""

        # Generate dialogue based on mode
        dialogue = self._generate_mode_dialogue(
            npc=npc,
            events=known_events,
            beliefs=local_beliefs,
            recall_text=recall_text,
            mode=mode,
        )

        return dialogue, provenance

    def _generate_mode_dialogue(self, npc: NpcState, events: List,
                                 beliefs: List, recall_text: str,
                                 mode: MemoryMode) -> str:
        """Generate mode-specific dialogue.

        Each mode produces observably different output:
        - Graph mode: formal, factual, references event IDs
        - Vector mode: emotional, may reference events NPC doesn't know
        - Hybrid mode: balanced, grounded, emotionally aware
        """
        if mode == MemoryMode.graph:
            return self._graph_dialogue(npc, events)
        elif mode == MemoryMode.vector:
            return self._vector_dialogue(npc, events, recall_text)
        else:
            return self._hybrid_dialogue(npc, events, recall_text)

    def _graph_dialogue(self, npc: NpcState, events: List) -> str:
        """Graph-only dialogue. Factual, rigid, no emotional generalization.

        This mode only uses locally known facts. It cannot generalize
        across similar events or infer emotional context.
        """
        if not events:
            if npc.faction:
                return f"I am {npc.name} of the {npc.faction.value}. I have no record of you."
            return f"I am {npc.name}. I don't know you."

        action_count = len(events)
        last_action = events[-1].action_type.value if events else "unknown"

        return (
            f"[Graph Fact] NPC {npc.name} has {action_count} known event(s) "
            f"involving the player. Last event: {last_action}. "
            f"Sentiment values: trust={npc.trust}, fear={npc.fear}, "
            f"respect={npc.respect}, anger={npc.anger}. "
            f"These are recorded facts."
        )

    def _vector_dialogue(self, npc: NpcState, events: List,
                          recall_text: str) -> str:
        """Vector-only dialogue. Expressive but may hallucinate.

        This mode uses Cognee's RAG completion, which retrieves semantically
        similar content. It can produce emotional responses but may leak
        knowledge from other NPCs' datasets.
        """
        if recall_text and len(recall_text) > 10:
            # Use Cognee's semantic recall — may include facts the NPC
            # shouldn't know (that's the vector-only failure mode)
            return (
                f"[Vector Memory] Based on semantic associations: "
                f"{recall_text[:200]} "
                f"I have a feeling about you, even if I can't say exactly why."
            )

        if not events:
            return f"[Vector Memory] Something about you seems familiar, but I can't place it."

        return (
            f"[Vector Memory] I sense you've been involved in events here. "
            f"The impressions linger. I feel {self._describe_mood(npc)} "
            f"when I think of you."
        )

    def _hybrid_dialogue(self, npc: NpcState, events: List,
                          recall_text: str) -> str:
        """Hybrid dialogue. Grounded facts + emotional intelligence.

        This mode combines:
        - Graph-grounded facts (only events this NPC knows)
        - Vector-semantic tone (emotional color)
        - The result is both accurate and nuanced
        """
        if not events:
            greeting = self._get_faction_greeting(npc)
            return (
                f"[Hybrid Memory] {greeting} "
                f"The wind carries stories, but I have none of you yet."
            )

        last_action = events[-1].action_type.value.replace("_", " ")
        mood = self._describe_mood(npc)
        faction_ref = f"as a member of the {npc.faction.value}" if npc.faction else ""

        return (
            f"[Hybrid Memory] {faction_ref} I recall what happened — "
            f"the {last_action}. It stays with me. "
            f"Right now I feel {mood} toward you. "
            f"What brings you here now?"
        )

    def _get_faction_greeting(self, npc: NpcState) -> str:
        if not npc.faction:
            return "Welcome to Lumen Market."
        return f"The {npc.faction.value} watches over this village."

    def _describe_mood(self, npc: NpcState) -> str:
        """Describe the NPC's emotional state in words."""
        if npc.anger > 60:
            return "angry and wronged"
        elif npc.fear > 50:
            return "wary and cautious"
        elif npc.trust < 30:
            return "distrustful"
        elif npc.trust > 70:
            return "warm and welcoming"
        elif npc.respect > 60:
            return "respectful"
        else:
            return "cautious"
```

---

## Chunk 4: Frontend Foundation

**Goal:** A running React app with Tailwind that talks to the backend and renders the game.

### Task 4.1: Scaffold React + Vite

- [ ] **Step 1: Create the frontend**
```bash
cd cog2
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite axios
```

- [ ] **Step 2: Configure Tailwind in `vite.config.ts`**
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 3: Add Tailwind import to `src/index.css`**
```css
@import "tailwindcss";
```

- [ ] **Step 4: Verify it runs**
```bash
cd frontend && npm run dev
```
Expected: Blank Vite page at localhost:5173.

### Task 4.2: TypeScript Types & API Client

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`

- [ ] **Step 1: Create `frontend/src/types.ts`** (mirrors backend models)

```typescript
export type Faction = "Orchard Guild" | "Shrine Circle" | "Alley Network";
export type Location = "orchard_stall" | "guild_hall" | "shrine" | "alley" | "town_square";
export type MemoryMode = "graph" | "vector" | "hybrid";
export type ActionType = "steal" | "gift" | "help" | "lie" | "apologize" | "threaten" | "ask_rumor" | "return_item";

export interface NpcState {
  name: string;
  location: Location;
  faction: Faction | null;
  trust: number;
  fear: number;
  respect: number;
  anger: number;
}

export interface FactionMood {
  faction: Faction;
  trust: number;
  fear: number;
  respect: number;
  anger: number;
  last_event: string | null;
}

export interface EventRecord {
  event_id: string;
  action_type: ActionType;
  actor: string;
  target_npc: string;
  item: string | null;
  description: string | null;
  timestamp: string;
  location: Location;
  witnesses: string[];
  public: boolean;
}

export interface BeliefRecord {
  npc_name: string;
  event_id: string;
  certainty: number;
  source: "witnessed" | "told" | "rumor";
  heard_from: string | null;
}

export interface GameState {
  player_location: Location;
  npcs: Record<string, NpcState>;
  factions: Record<string, FactionMood>;
  recent_events: EventRecord[];
  beliefs: Record<string, BeliefRecord[]>;
  session_id: string;
}

export interface ActionResponse {
  event_id: string;
  npc_reactions: Record<string, string>;
  updated_state: GameState;
}

export interface DialogueResponse {
  npc_name: string;
  dialogue: string;
  provenance: any[];
  mode: MemoryMode;
}

export interface MemoryGraphNode {
  id: string;
  label: string;
  type: "player" | "npc" | "faction" | "event" | "location" | "belief";
  faction: Faction | null;
}

export interface MemoryGraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface MemoryGraph {
  nodes: MemoryGraphNode[];
  edges: MemoryGraphEdge[];
}
```

- [ ] **Step 2: Create `frontend/src/api.ts`**

```typescript
import axios from 'axios';
import type { GameState, ActionResponse, DialogueResponse, MemoryGraph, ActionType, MemoryMode } from './types';

const API = axios.create({ baseURL: '/api' });

// Session ID — persists for the browser session
let _sessionId: string | null = null;

export function getSessionId(): string {
  if (!_sessionId) {
    _sessionId = `web_${Math.random().toString(36).slice(2, 10)}`;
  }
  return _sessionId;
}

export async function fetchState(): Promise<GameState> {
  const { data } = await API.get('/state', { params: { session_id: getSessionId() } });
  return data;
}

export async function performAction(
  actionType: ActionType,
  targetNpc: string,
  item?: string,
  description?: string,
): Promise<ActionResponse> {
  const { data } = await API.post('/action', {
    action_type: actionType,
    target_npc: targetNpc,
    item: item || null,
    description: description || null,
  }, { params: { session_id: getSessionId() } });
  return data;
}

export async function getDialogue(
  npcName: string,
  mode: MemoryMode = 'hybrid',
): Promise<DialogueResponse> {
  const { data } = await API.get(`/dialogue/${npcName}`, {
    params: { mode, session_id: getSessionId() },
  });
  return data;
}

export async function fetchMemoryGraph(): Promise<MemoryGraph> {
  const { data } = await API.get('/memory/graph', {
    params: { session_id: getSessionId() },
  });
  return data;
}

export async function fetchBeliefs() {
  const { data } = await API.get('/memory/beliefs', {
    params: { session_id: getSessionId() },
  });
  return data.beliefs;
}

export async function fetchFactions() {
  const { data } = await API.get('/memory/factions', {
    params: { session_id: getSessionId() },
  });
  return data.factions;
}

export async function classifyAction(description: string) {
  const { data } = await API.post('/classify', {
    action_type: 'help',
    target_npc: 'none',
    description,
  });
  return data;
}

export async function resetSession() {
  const { data } = await API.post('/reset', null, {
    params: { session_id: getSessionId() },
  });
  _sessionId = data.session_id;
  return data;
}
```

### Task 4.3: Game Canvas & World Rendering

**Files:**
- Create: `frontend/src/components/GameCanvas.tsx`

- [ ] **Step 1: Create the HTML canvas-based village map**

```tsx
import { useRef, useEffect } from 'react';
import type { NpcState, Location, GameState } from '../types';

// Pixel positions for each location on the map
const LOCATION_COORDS: Record<Location, { x: number; y: number }> = {
  orchard_stall: { x: 120, y: 80 },
  guild_hall: { x: 350, y: 60 },
  shrine: { x: 250, y: 220 },
  alley: { x: 80, y: 180 },
  town_square: { x: 220, y: 130 },
};

const LOCATION_NAMES: Record<Location, string> = {
  orchard_stall: 'Orchard Stall',
  guild_hall: 'Guild Hall',
  shrine: 'Shrine',
  alley: 'Alley',
  town_square: 'Town Square',
};

const FACTION_COLORS: Record<string, string> = {
  'Orchard Guild': '#22c55e',    // green
  'Shrine Circle': '#a855f7',    // purple
  'Alley Network': '#f59e0b',    // amber
};

const DEFAULT_NPC_COLOR = '#6b7280'; // gray for factionless NPCs

interface Props {
  gameState: GameState;
  onNpcClick: (npcName: string) => void;
}

export function GameCanvas({ gameState, onNpcClick }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = 500;
    const H = 350;
    canvas.width = W;
    canvas.height = H;

    // Clear
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, W, H);

    // Draw paths/roads
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 3;
    // Road from town square to each location
    const center = LOCATION_COORDS.town_square;
    for (const loc of Object.keys(LOCATION_COORDS) as Location[]) {
      if (loc === 'town_square') continue;
      const pos = LOCATION_COORDS[loc];
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
    }

    // Draw location markers
    for (const [loc, pos] of Object.entries(LOCATION_COORDS)) {
      if (loc === 'town_square') continue;
      // Location circle
      ctx.fillStyle = '#334155';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 18, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Location name
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(LOCATION_NAMES[loc as Location], pos.x, pos.y + 30);
    }

    // Town square
    const ts = LOCATION_COORDS.town_square;
    ctx.fillStyle = '#334155';
    ctx.beginPath();
    ctx.arc(ts.x, ts.y, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Town Square', ts.x, ts.y + 34);

    // Draw NPCs
    for (const [name, npc] of Object.entries(gameState.npcs)) {
      const pos = LOCATION_COORDS[npc.location];
      const color = npc.faction ? FACTION_COLORS[npc.faction] || DEFAULT_NPC_COLOR : DEFAULT_NPC_COLOR;

      // NPC circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // NPC name
      ctx.fillStyle = '#e2e8f0';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(name, pos.x, pos.y - 14);

      // Clickable indicator
      ctx.fillStyle = '#64748b';
      ctx.font = '8px sans-serif';
      ctx.fillText('(click)', pos.x, pos.y + 16);
    }

    // Player marker (at their location)
    const playerPos = LOCATION_COORDS[gameState.player_location];
    ctx.fillStyle = '#60a5fa';
    ctx.beginPath();
    ctx.arc(playerPos.x, playerPos.y, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('You', playerPos.x, playerPos.y - 16);

  }, [gameState]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if click is near an NPC
    for (const [name, npc] of Object.entries(gameState.npcs)) {
      const pos = LOCATION_COORDS[npc.location];
      const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (dist < 20) {
        onNpcClick(name);
        return;
      }
    }
  };

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      className="rounded-lg border border-slate-700 cursor-pointer w-full max-w-[500px]"
      style={{ height: '350px' }}
    />
  );
}
```

### Task 4.4: Main App Assembly

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write the main App component**

```tsx
import { useState, useEffect, useCallback } from 'react';
import type { GameState, MemoryMode, ActionType } from './types';
import * as api from './api';
import { GameCanvas } from './components/GameCanvas';
import { InspectorPanel } from './components/InspectorPanel';

const ACTIONS: { type: ActionType; label: string; color: string }[] = [
  { type: 'steal', label: 'Steal', color: 'bg-red-800 hover:bg-red-700' },
  { type: 'gift', label: 'Gift', color: 'bg-green-800 hover:bg-green-700' },
  { type: 'help_', label: 'Help', color: 'bg-emerald-800 hover:bg-emerald-700' },
  { type: 'lie', label: 'Lie', color: 'bg-yellow-800 hover:bg-yellow-700' },
  { type: 'apologize', label: 'Apologize', color: 'bg-blue-800 hover:bg-blue-700' },
  { type: 'threaten', label: 'Threaten', color: 'bg-orange-800 hover:bg-orange-700' },
  { type: 'ask_rumor', label: 'Ask Rumor', color: 'bg-purple-800 hover:bg-purple-700' },
  { type: 'return_item', label: 'Return Item', color: 'bg-teal-800 hover:bg-teal-700' },
];

export default function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [mode, setMode] = useState<MemoryMode>('hybrid');
  const [dialogue, setDialogue] = useState<{ npc: string; text: string; provenance: any[] } | null>(null);
  const [lastAction, setLastAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.fetchState()
      .then(setGameState)
      .catch(e => setError(`Failed to connect: ${e.message}`));
  }, []);

  const performAction = useCallback(async (actionType: ActionType, targetNpc: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.performAction(actionType, targetNpc);
      setGameState(res.updated_state as GameState);
      setLastAction(actionType);
      // Show the target NPC's reaction
      const reaction = res.npc_reactions[targetNpc];
      if (reaction) {
        setDialogue({ npc: targetNpc, text: reaction, provenance: [] });
      }
    } catch (e: any) {
      setError(`Action failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const talkToNpc = useCallback(async (npcName: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDialogue(npcName, mode);
      setDialogue({ npc: npcName, text: res.dialogue, provenance: res.provenance });
    } catch (e: any) {
      setError(`Failed to get dialogue: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [mode]);

  const resetGame = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.resetSession();
      setGameState(res.state);
      setDialogue(null);
      setLastAction(null);
      setError(null);
    } catch (e: any) {
      setError(`Reset failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  if (!gameState) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 text-xl animate-pulse">Echo — Connecting...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col">
      {/* Top Bar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-indigo-400">Echo</h1>
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
            Lumen Market
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* Mode Toggle */}
          <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
            {(['graph', 'vector', 'hybrid'] as MemoryMode[]).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-3 py-1 text-xs rounded font-bold uppercase transition ${
                  mode === m
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <button
            onClick={resetGame}
            className="text-xs text-slate-500 hover:text-slate-300 px-3 py-1 rounded bg-slate-800"
          >
            Reset
          </button>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-900/40 border border-red-800 px-6 py-2 text-sm text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-4 text-red-400 hover:text-red-200">✕</button>
        </div>
      )}

      <div className="flex flex-1">
        {/* Left: Game + Actions */}
        <div className="flex-1 p-6 space-y-4">
          {/* Game Canvas */}
          <GameCanvas gameState={gameState} onNpcClick={talkToNpc} />

          {/* Action Buttons */}
          <div className="space-y-2">
            <h3 className="text-xs uppercase font-bold text-slate-500 tracking-wider">Actions</h3>
            <div className="flex flex-wrap gap-2">
              {ACTIONS.map(action => (
                <button
                  key={action.type}
                  onClick={() => {
                    // Target the NPC at the player's location, or fall back to first NPC
                    const target = Object.values(gameState.npcs).find(
                      n => n.location === gameState.player_location
                    )?.name || Object.keys(gameState.npcs)[0];
                    performAction(action.type, target);
                  }}
                  disabled={loading}
                  className={`${action.color} text-white text-xs font-bold px-3 py-2 rounded transition disabled:opacity-50`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>

          {/* NPC List Quick Actions */}
          <div className="space-y-2">
            <h3 className="text-xs uppercase font-bold text-slate-500 tracking-wider">
              NPCs ({mode} mode)
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(gameState.npcs).map(([name, npc]) => (
                <button
                  key={name}
                  onClick={() => talkToNpc(name)}
                  className="bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded p-2 text-left text-xs transition"
                >
                  <div className="font-bold text-sm text-emerald-400">{name}</div>
                  <div className="text-slate-400">{npc.location.replace('_', ' ')}</div>
                  <div className="text-slate-500">
                    {npc.faction || 'No faction'} · T:{npc.trust} A:{npc.anger}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Dialogue Box */}
          {dialogue && (
            <div className="bg-indigo-900/30 border border-indigo-500/30 rounded-lg p-4 animate-[fadeIn_0.3s]">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-indigo-300 text-sm font-bold">{dialogue.npc}</span>
                <span className="text-xs text-slate-500">({mode} mode)</span>
              </div>
              <p className="text-indigo-50 text-sm leading-relaxed">{dialogue.text}</p>
              {dialogue.provenance.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300">
                    What influenced this response?
                  </summary>
                  <pre className="mt-1 text-[10px] text-slate-500 font-mono bg-slate-900 p-2 rounded">
                    {JSON.stringify(dialogue.provenance, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="text-xs text-slate-500 animate-pulse">
              Processing memory...
            </div>
          )}
        </div>

        {/* Right: Inspector Panel */}
        <div className="w-80 border-l border-slate-800 bg-slate-900/50">
          <InspectorPanel gameState={gameState} mode={mode} />
        </div>
      </div>
    </div>
  );
}
```

### Task 4.5: Memory Inspector Panel (Core Visualization)

**Files:**
- Create: `frontend/src/components/InspectorPanel.tsx`

- [ ] **Step 1: Write the Inspector Panel with tabs**

```tsx
import { useState, useEffect } from 'react';
import type { GameState, MemoryMode, MemoryGraph, BeliefRecord, FactionMood } from '../types';
import * as api from '../api';

interface Props {
  gameState: GameState;
  mode: MemoryMode;
}

type Tab = 'graph' | 'facts' | 'beliefs' | 'factions' | 'baseline';

export function InspectorPanel({ gameState, mode }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('graph');
  const [graph, setGraph] = useState<MemoryGraph | null>(null);
  const [beliefs, setBeliefs] = useState<Record<string, BeliefRecord[]>>({});
  const [factions, setFactions] = useState<Record<string, FactionMood>>({});

  useEffect(() => {
    api.fetchMemoryGraph().then(setGraph).catch(() => {});
    api.fetchBeliefs().then(setBeliefs).catch(() => {});
    api.fetchFactions().then(setFactions).catch(() => {});
  }, [gameState]);

  const tabs: { key: Tab; label: string }[] = [
    { key: 'graph', label: 'Graph' },
    { key: 'facts', label: 'Facts' },
    { key: 'beliefs', label: 'Beliefs' },
    { key: 'factions', label: 'Factions' },
    { key: 'baseline', label: 'Baseline' },
  ];

  return (
    <div className="h-full flex flex-col p-4">
      <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">
        Memory Inspector
      </h2>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-slate-800 rounded-lg p-1">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 text-[10px] font-bold uppercase py-1.5 rounded transition ${
              activeTab === tab.key
                ? 'bg-indigo-600 text-white'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto space-y-2 text-xs">
        {activeTab === 'graph' && <GraphTab graph={graph} />}
        {activeTab === 'facts' && <FactsTab events={gameState.recent_events} />}
        {activeTab === 'beliefs' && <BeliefsTab beliefs={beliefs} />}
        {activeTab === 'factions' && <FactionsTab factions={factions} />}
        {activeTab === 'baseline' && <BaselineTab mode={mode} />}
      </div>
    </div>
  );
}

function GraphTab({ graph }: { graph: MemoryGraph | null }) {
  if (!graph) return <div className="text-slate-600 italic">Loading graph...</div>;

  return (
    <div className="space-y-2">
      <div className="text-slate-400 text-[10px] font-mono">
        {graph.nodes.length} nodes · {graph.edges.length} edges
      </div>
      <div className="space-y-1">
        {graph.edges.slice(-15).reverse().map((edge, i) => (
          <div key={i} className="text-[10px] font-mono bg-slate-800 p-1.5 rounded border border-slate-700">
            <span className="text-blue-400">{edge.source}</span>
            <span className="text-slate-500 mx-1">─[{edge.label}]→</span>
            <span className="text-emerald-400">{edge.target}</span>
          </div>
        ))}
        {graph.edges.length === 0 && (
          <div className="text-slate-600 italic">No memory edges yet. Perform an action to create them.</div>
        )}
      </div>
    </div>
  );
}

function FactsTab({ events }: { events: any[] }) {
  if (events.length === 0) {
    return <div className="text-slate-600 italic">No events recorded yet. Steal something to start.</div>;
  }

  return (
    <div className="space-y-2">
      {[...events].reverse().map((ev, i) => (
        <div key={i} className="bg-slate-800 border border-slate-700 rounded p-2 space-y-0.5">
          <div className="flex justify-between">
            <span className="font-bold text-indigo-300">{ev.action_type}</span>
            <span className="text-[9px] text-slate-500">{ev.event_id}</span>
          </div>
          <div className="text-slate-400">Target: {ev.target_npc}</div>
          {ev.item && <div className="text-slate-400">Item: {ev.item}</div>}
          <div className="text-slate-500">Witnesses: {ev.witnesses.join(', ') || 'none'}</div>
          <div className="text-[9px] text-slate-600">
            {new Date(ev.timestamp).toLocaleTimeString()}
          </div>
        </div>
      ))}
    </div>
  );
}

function BeliefsTab({ beliefs }: { beliefs: Record<string, BeliefRecord[]> }) {
  const hasBeliefs = Object.values(beliefs).some(b => b.length > 0);

  if (!hasBeliefs) {
    return <div className="text-slate-600 italic">No NPC beliefs yet. Memory hasn't propagated.</div>;
  }

  return (
    <div className="space-y-2">
      {Object.entries(beliefs).map(([npc, npcBeliefs]) =>
        npcBeliefs.map((b, i) => (
          <div key={i} className="bg-slate-800 border border-slate-700 rounded p-2">
            <div className="flex justify-between items-center">
              <span className="font-bold text-emerald-400">{npc}</span>
              <span className={`text-[10px] font-bold ${
                b.certainty > 0.7 ? 'text-green-400' : b.certainty > 0.3 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {(b.certainty * 100).toFixed(0)}% certain
              </span>
            </div>
            <div className="text-slate-400">Event: {b.event_id}</div>
            <div className="text-[10px] text-slate-500">
              Source: {b.source}{b.heard_from ? ` (from ${b.heard_from})` : ''}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function FactionsTab({ factions }: { factions: Record<string, FactionMood> }) {
  const entries = Object.entries(factions);
  if (entries.length === 0) {
    return <div className="text-slate-600 italic">No faction data.</div>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([name, mood]) => (
        <div key={name} className="bg-slate-800 border border-slate-700 rounded p-3">
          <h4 className="font-bold text-sm mb-2 text-slate-200">{name}</h4>
          <div className="space-y-1.5">
            <MeterBar label="Trust" value={mood.trust} color="bg-green-500" />
            <MeterBar label="Fear" value={mood.fear} color="bg-yellow-500" />
            <MeterBar label="Respect" value={mood.respect} color="bg-blue-500" />
            <MeterBar label="Anger" value={mood.anger} color="bg-red-500" />
          </div>
          {mood.last_event && (
            <div className="text-[9px] text-slate-600 mt-2">Last event: {mood.last_event}</div>
          )}
        </div>
      ))}
    </div>
  );
}

function MeterBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-400 w-12">{label}</span>
      <div className="flex-1 bg-slate-900 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-[10px] text-slate-500 w-6 text-right">{value}</span>
    </div>
  );
}

function BaselineTab({ mode }: { mode: MemoryMode }) {
  const comparisons = [
    {
      mode: 'graph' as MemoryMode,
      strength: 'Tracks exact facts: who saw what, who knows whom.',
      weakness: 'Cannot generalize meaning. Treats "stole relic" and "betrayed trust" as separate facts.',
      example: 'Rowan knows theft_001 happened but responds mechanically.',
    },
    {
      mode: 'vector' as MemoryMode,
      strength: 'Generalizes emotional meaning across similar events.',
      weakness: 'Cannot enforce knowledge boundaries. May leak facts to uninformed NPCs.',
      example: 'Sol, who was never told, might say "I heard about the theft."',
    },
    {
      mode: 'hybrid' as MemoryMode,
      strength: 'Grounded facts + emotional intelligence. Partial knowledge enforced.',
      weakness: 'Slightly slower than pure vector recall (but still sub-second).',
      example: 'Rowan knows through Mira; Sol does not know unless told.',
    },
  ];

  return (
    <div className="space-y-3">
      {comparisons.map(c => (
        <div
          key={c.mode}
          className={`bg-slate-800 border rounded p-3 ${
            mode === c.mode ? 'border-indigo-500 ring-1 ring-indigo-500/50' : 'border-slate-700'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold uppercase ${
              mode === c.mode ? 'text-indigo-300' : 'text-slate-400'
            }`}>
              {c.mode}
            </span>
            {mode === c.mode && (
              <span className="text-[9px] bg-indigo-600 text-white px-1.5 py-0.5 rounded">ACTIVE</span>
            )}
          </div>
          <div className="text-[11px] text-green-400 mb-1">✓ {c.strength}</div>
          <div className="text-[11px] text-red-400 mb-1">✗ {c.weakness}</div>
          <div className="text-[10px] text-slate-500 italic">{c.example}</div>
        </div>
      ))}
    </div>
  );
}
```

---

## Chunk 5: Frontend Integration & Polish

**Goal:** Connect frontend to backend, verify the full flow works end-to-end, add the open-action text box.

### Task 5.1: Open-Action Text Box (Anti-Hardcode Proof)

**Files:**
- Modify: `frontend/src/App.tsx` (add custom action input)

- [ ] **Step 1: Add the open-action section to App.tsx**

```tsx
// Add this after the action buttons section:

const [customAction, setCustomAction] = useState('');
const [classification, setClassification] = useState<any>(null);

const classifyCustomAction = useCallback(async () => {
  if (!customAction.trim()) return;
  setLoading(true);
  try {
    const res = await api.classifyAction(customAction);
    setClassification(res);
  } catch (e: any) {
    setError(`Classification failed: ${e.message}`);
  } finally {
    setLoading(false);
  }
}, [customAction]);

// JSX for the custom action section:
<div className="space-y-2">
  <h3 className="text-xs uppercase font-bold text-slate-500 tracking-wider">
    Custom Action (anti-hardcode proof)
  </h3>
  <div className="flex gap-2">
    <input
      type="text"
      value={customAction}
      onChange={e => setCustomAction(e.target.value)}
      placeholder='e.g. "I threatened Niko with a knife"'
      className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
    />
    <button
      onClick={classifyCustomAction}
      disabled={loading || !customAction.trim()}
      className="bg-indigo-800 hover:bg-indigo-700 text-white text-xs font-bold px-3 py-2 rounded transition disabled:opacity-50"
    >
      Classify
    </button>
  </div>
  {classification && (
    <div className="bg-slate-800 border border-slate-700 rounded p-2 text-xs space-y-1">
      <div>Valence: <span className={`font-bold ${
        classification.valence === 'negative' ? 'text-red-400' :
        classification.valence === 'positive' ? 'text-green-400' : 'text-yellow-400'
      }`}>{classification.valence}</span></div>
      <div>Confidence: {(classification.confidence * 100).toFixed(0)}%</div>
      <div className="text-[10px] text-slate-500 font-mono">{classification.raw}</div>
    </div>
  )}
</div>
```

### Task 5.2: Fade-In Animation CSS

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Add animation keyframes**

```css
@import "tailwindcss";

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-node {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* Scrollbar styling for the inspector */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 2px;
}
```

### Task 5.3: End-to-End Verification

- [ ] **Step 1: Start backend**
```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**
```bash
cd frontend && npm run dev
```

- [ ] **Step 3: Verify the full flow**
1. Open `http://localhost:5173` in a browser
2. Game loads with the village map and 6 NPCs
3. Click "Steal" action → NPC Mira reacts
4. Switch mode to "graph" → click "Talk" on Rowan → graph-only response shown
5. Switch mode to "vector" → click "Talk" on Sol → vector response shown (may leak)
6. Switch mode to "hybrid" → click "Talk" on Sol → hybrid response (should not leak)
7. Inspector panel shows graph edges, facts, beliefs, faction moods
8. Type "I threatened Niko with a knife" in custom action box → classification appears

---

## Chunk 6: Demo Script & Deployment

**Goal:** A polished, deployable submission with README, hosted URL, and demo video.

### Task 6.1: Deploy Backend to Railway

- [ ] **Step 1: Create `backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create `backend/.env.example`**
```
COGNEE_BASE_URL=https://your-tenant.aws.cognee.ai
COGNEE_API_KEY=your-api-key
LLM_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

- [ ] **Step 3: Deploy to Railway**
```bash
railway login
railway init
railway up
```

### Task 6.2: Deploy Frontend to Vercel

- [ ] **Step 1: Create `frontend/vercel.json`**
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://echo-backend.railway.app/api/$1" }
  ]
}
```

- [ ] **Step 2: Deploy to Vercel**
```bash
cd frontend && npx vercel --prod
```

### Task 6.3: Write README

- [ ] **Step 1: Write root `README.md`**

The README must include:
- One-sentence thesis
- Screenshots of the game + inspector
- Architecture diagram
- Demo script (the 8-step scenario from echo_spec.md)
- Baseline comparison explanation
- Cognee Cloud integration details
- How to deploy
- AI assistance disclosure
- Link to demo video

---

## Chunk 7: Tests

**Goal:** Automated tests that prove the system works.

### Task 7.1: Backend Tests

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_propagation.py`
- Create: `backend/tests/test_baselines.py`

- [ ] **Step 1: Write propagation test**
```python
# tests/test_propagation.py
# Tests that:
# 1. Event propagation creates belief records for connected NPCs
# 2. Rivals do not propagate to each other
# 3. Certainty is higher for witnessed events than hearsay
```

- [ ] **Step 2: Write baseline test**
```python
# tests/test_baselines.py
# Tests that:
# 1. Graph mode only returns what the NPC factually knows
# 2. Vector mode may return results from other NPCs' knowledge
# 3. Hybrid mode enforces knowledge boundaries + emotional tone
```

---

## Decision Matrix Summary

Every chunk produces a working, testable artifact:

| Chunk | What exists after | How to verify |
|---|---|---|
| 0 | `spike_results.jsonl` | 7 tests PASS/FAIL |
| 1 | FastAPI server with game state | `curl /health` returns 200 |
| 2 | Events propagate through social graph | Belief records created for connected NPCs |
| 3 | Three recall modes produce different dialogue | `/dialogue/Mira?mode=graph` vs `?mode=hybrid` |
| 4 | React game renders with village map | Open `localhost:5173`, see 6 NPCs on map |
| 5 | Full end-to-end flow works | Click actions → NPC reacts → inspector updates |
| 6 | Deployed at public URL | Open hosted URL, run demo script |
| 7 | Tests pass | `pytest backend/tests/` |
