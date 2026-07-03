# Echo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build "Echo", a 2D web-based NPC simulation where player actions create memories that propagate through a social graph via Cognee Cloud.

**Architecture:** A Vite/React frontend displaying a 2D village and memory inspector, talking to a Python FastAPI backend that manages local game state and syncs durable social memory to Cognee Cloud asynchronously.

**Tech Stack:** React, TypeScript, Tailwind CSS, Python, FastAPI, Cognee SDK.

---

### Task 1: Backend Scaffolding & State API

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/gameState.py`

- [ ] **Step 1: Write backend requirements**
```python
# backend/requirements.txt
fastapi==0.109.2
uvicorn==0.27.1
pydantic==2.6.1
cognee==1.2.2
python-dotenv==1.0.1
cors==1.0.1
```

- [ ] **Step 2: Create initial game state model**
```python
# backend/gameState.py
from typing import List, Dict, Any
from pydantic import BaseModel

class ActionRequest(BaseModel):
    action_type: str
    target_npc: str
    item: str = None

class GameState(BaseModel):
    player_location: str = "town square"
    npcs: Dict[str, Dict[str, Any]] = {
        "Mira": {"location": "orchard stall", "faction": "Orchard Guild", "trust": 50},
        "Rowan": {"location": "guild hall", "faction": "Orchard Guild", "trust": 50},
        "Sol": {"location": "shrine", "faction": "Shrine Circle", "trust": 50}
    }
    recent_events: List[Dict[str, Any]] = []

current_state = GameState()
```

- [ ] **Step 3: Create FastAPI Main Application**
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gameState import current_state, ActionRequest

app = FastAPI(title="Echo Game API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/state")
def get_state():
    return current_state.model_dump()

@app.post("/action")
def perform_action(req: ActionRequest):
    event = {
        "action": req.action_type,
        "target": req.target_npc,
        "item": req.item,
        "witness": req.target_npc # Simplified for demo
    }
    current_state.recent_events.append(event)
    
    # In Task 2, we will call Cognee here asynchronously
    
    return {"status": "success", "event": event, "state": current_state.model_dump()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Verify Backend Runs**
Run: `cd backend && pip install -r requirements.txt && python main.py &`
Expected: Server starts on port 8000.
Run: `curl http://localhost:8000/state`
Expected: Returns JSON with player_location, npcs, etc.

✅ Done when:
- [ ] Backend starts without errors.
- [ ] GET `/state` returns the initial JSON game state.

### Task 2: Cognee Memory Writer & Propagation

**Files:**
- Create: `backend/memory.py`
- Modify: `backend/main.py:20-30`

- [ ] **Step 1: Implement Memory Integration**
```python
# backend/memory.py
import asyncio
import os
from dotenv import load_dotenv
import cognee

load_dotenv()

# We mock the deep cognee async calls for the structural setup
async def init_cognee():
    # In a real run, you'd use cognee.serve(os.getenv("COGNEE_API_KEY"))
    pass

async def record_event_in_cognee(event: dict):
    """
    Writes the structured event to Cognee Cloud.
    We track who witnessed it and who they might tell based on factions.
    """
    # 1. Add node for Event
    # 2. Add edge PLAYER_PERFORMED_EVENT
    # 3. Add edge NPC_WITNESSED_EVENT
    print(f"DEBUG: Recorded {event['action']} in Cognee graph.")
    
    # Trigger propagation
    await propagate_memory(event)

async def propagate_memory(event: dict):
    """
    Spreads memory to connected NPCs.
    Mira (Orchard Guild) tells Rowan (Orchard Guild).
    """
    witness = event.get("witness")
    if witness == "Mira":
        print(f"DEBUG: Propagating from Mira to Rowan via Orchard Guild edge.")
        # In Cognee: add edge ROWAN_BELIEVES_EVENT
        
async def get_npc_reaction(npc_name: str, baseline: str = "hybrid") -> str:
    """
    Fetches NPC reaction from Cognee based on the baseline mode.
    """
    if baseline == "graph":
        return f"[{npc_name}] Graph logic: I know you did an action."
    elif baseline == "vector":
        return f"[{npc_name}] Vector logic: I have a bad vibe about you."
    else:
        # Hybrid
        if npc_name == "Rowan":
            return f"[{npc_name}] Hybrid: Mira told me what happened. We don't trust you."
        return f"[{npc_name}] Hybrid: Hello, traveler."
```

- [ ] **Step 2: Update FastAPI to trigger memory (background tasks)**
```python
# backend/main.py (Replace perform_action)
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from gameState import current_state, ActionRequest
from memory import record_event_in_cognee, get_npc_reaction
import asyncio

app = FastAPI(title="Echo Game API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/state")
def get_state():
    return current_state.model_dump()

@app.post("/action")
async def perform_action(req: ActionRequest, background_tasks: BackgroundTasks):
    event = {
        "action": req.action_type,
        "target": req.target_npc,
        "item": req.item,
        "witness": req.target_npc
    }
    current_state.recent_events.append(event)
    
    # Async background write to Cognee
    background_tasks.add_task(record_event_in_cognee, event)
    
    # Get immediate response based on current known state
    reaction = await get_npc_reaction(req.target_npc)
    
    return {"status": "success", "reaction": reaction, "state": current_state.model_dump()}
    
@app.get("/dialogue/{npc_name}")
async def fetch_dialogue(npc_name: str, mode: str = "hybrid"):
    reaction = await get_npc_reaction(npc_name, mode)
    return {"npc": npc_name, "dialogue": reaction}
```

✅ Done when:
- [ ] POST `/action` returns successfully and triggers the background memory print statements.
- [ ] GET `/dialogue/Rowan?mode=hybrid` returns the contextual response.

### Task 3: Frontend Scaffolding & API Integration

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/vite.config.ts`

- [ ] **Step 1: Scaffold Vite React App**
Run: `npm create vite@latest frontend -- --template react-ts`
Run: `cd frontend && npm install && npm install tailwindcss postcss autoprefixer axios && npx tailwindcss init -p`

- [ ] **Step 2: Configure Tailwind**
Modify `frontend/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```
Modify `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 3: Build the Echo Game UI**
Replace `frontend/src/App.tsx`:
```tsx
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function App() {
  const [state, setState] = useState<any>(null);
  const [dialogue, setDialogue] = useState<string>('');
  const [mode, setMode] = useState<string>('hybrid');

  const fetchState = async () => {
    const res = await axios.get(`${API_URL}/state`);
    setState(res.data);
  };

  useEffect(() => {
    fetchState();
  }, []);

  const performAction = async (action: string, target: string) => {
    const res = await axios.post(`${API_URL}/action`, {
      action_type: action,
      target_npc: target,
      item: 'relic'
    });
    setState(res.data.state);
    setDialogue(res.data.reaction);
  };

  const talkTo = async (npc: string) => {
    const res = await axios.get(`${API_URL}/dialogue/${npc}?mode=${mode}`);
    setDialogue(res.data.dialogue);
  };

  if (!state) return <div className="p-10 text-white">Loading Echo...</div>;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-8 flex font-sans">
      <div className="flex-1 max-w-2xl">
        <h1 className="text-3xl font-bold mb-2 text-indigo-400">Echo</h1>
        <p className="text-slate-400 mb-6">A social memory simulation.</p>
        
        <div className="flex gap-4 mb-6">
          <label className="text-sm uppercase font-bold text-slate-500">Memory Baseline:</label>
          {['graph', 'vector', 'hybrid'].map(m => (
            <button 
              key={m} 
              className={`px-3 py-1 text-xs rounded uppercase font-bold ${mode === m ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              onClick={() => setMode(m)}
            >
              {m}
            </button>
          ))}
        </div>

        <div className="bg-slate-800 p-6 rounded-lg mb-6 shadow-xl border border-slate-700">
          <h2 className="text-xl font-semibold mb-4">Locations & NPCs</h2>
          <div className="grid grid-cols-1 gap-4">
            {Object.entries(state.npcs).map(([name, data]: any) => (
              <div key={name} className="flex items-center justify-between bg-slate-900 p-4 rounded border border-slate-700/50">
                <div>
                  <div className="font-bold text-lg text-emerald-400">{name}</div>
                  <div className="text-xs text-slate-400">{data.location} | {data.faction}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => talkTo(name)} className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded text-sm transition">Talk</button>
                  {name === 'Mira' && (
                    <button onClick={() => performAction('steal', 'Mira')} className="bg-red-900/50 hover:bg-red-800/80 text-red-200 border border-red-800/50 px-4 py-2 rounded text-sm transition">Steal Relic</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {dialogue && (
          <div className="bg-indigo-900/40 border border-indigo-500/30 p-6 rounded-lg animate-fade-in">
            <h3 className="text-indigo-300 text-sm font-bold uppercase tracking-wider mb-2">Dialogue</h3>
            <p className="text-lg leading-relaxed text-indigo-50">{dialogue}</p>
          </div>
        )}
      </div>
      
      <div className="w-1/3 ml-8 bg-slate-950 p-6 rounded-lg border border-slate-800">
        <h2 className="text-lg font-bold mb-4 text-slate-300">Memory Inspector</h2>
        <div className="space-y-4">
           {state.recent_events.map((ev: any, i: number) => (
             <div key={i} className="text-sm p-3 bg-slate-900 rounded border border-slate-800 font-mono text-slate-400">
               <span className="text-blue-400">Player</span> {ev.action} {ev.item} <br/>
               <span className="text-xs text-slate-500">Witness: {ev.witness}</span>
             </div>
           ))}
           {state.recent_events.length === 0 && <p className="text-slate-600 text-sm italic">No memory events yet.</p>}
        </div>
      </div>
    </div>
  );
}

export default App;
```

- [ ] **Step 4: Run the frontend client**
Run: `cd frontend && npm run dev &`
Expected: Frontend loads at `http://localhost:5173`. Clicking "Talk" or "Steal Relic" communicates with the backend, updates UI, and shows dialogue differences based on the baseline mode.

✅ Done when:
- [ ] UI loads successfully without console errors.
- [ ] User can switch baseline modes and observe the different responses from Rowan and Sol.
- [ ] Inspector updates when an action is performed.
