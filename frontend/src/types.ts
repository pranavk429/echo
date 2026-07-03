export type ActionType = "steal" | "gift" | "help" | "lie" | "apologize" | "threaten" | "ask_rumor" | "return_item";
export type MemoryMode = "graph" | "vector" | "hybrid";
export type Location = "orchard_stall" | "guild_hall" | "shrine" | "alley" | "town_square";
export type Faction = "Orchard Guild" | "Shrine Circle" | "Alley Network";
export type RelationshipType = "ally" | "rival" | "neutral";
 
export interface NpcState {
  name: string;
  location: Location;
  faction: Faction | null;  // Vale and Ilya have null faction
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
  session_id: string;
  beliefs: Record<string, BeliefRecord[]>;
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
