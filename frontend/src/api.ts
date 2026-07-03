import axios from 'axios';
import type { GameState, ActionResponse, DialogueResponse, MemoryGraph, ActionType, MemoryMode } from './types';
 
const API = axios.create({ baseURL: '/api' });
 
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
 
export async function getDialogue(npcName: string, mode: MemoryMode = 'hybrid'): Promise<DialogueResponse> {
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
