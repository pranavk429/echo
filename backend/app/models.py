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
    faction: Optional[Faction]
    trust: float  # 0-100
    fear: float  # 0-100
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
    faction: Optional[Faction] = None


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
    beliefs: Dict[str, List[BeliefRecord]] = {}
