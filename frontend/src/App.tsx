import { useState, useEffect, useCallback } from 'react';
import type { GameState, MemoryMode, ActionType, Location } from './types';
import * as api from './api';
import { GameCanvas } from './components/GameCanvas';
import { ActionPanel } from './components/ActionPanel';
import { DialogueBox } from './components/DialogueBox';
import { InspectorPanel } from './components/InspectorPanel';
import { LocationBar } from './components/LocationBar';
import { BaselineComparison } from './components/BaselineComparison';

export default function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [playerLocation, setPlayerLocation] = useState<Location>('town_square');
  const [mode, setMode] = useState<MemoryMode>('hybrid');
  const [dialogue, setDialogue] = useState<{ npc: string; text: string; provenance: any[]; mode: MemoryMode } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [classification, setClassification] = useState<any>(null);

  // Baseline Comparison Modal State
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [compareNpcName, setCompareNpcName] = useState('Mira');

  // Fetch initial game state
  useEffect(() => {
    setLoading(true);
    api.fetchState()
      .then(state => {
        setGameState(state);
        setPlayerLocation(state.player_location);
        setError(null);
      })
      .catch(e => {
        setError(`Failed to connect to backend: ${e.message}. Is the backend running?`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // Merge local player location state into backend game state
  const mergedGameState = gameState ? {
    ...gameState,
    player_location: playerLocation
  } : null;

  // Perform a regular action (optionally with selected item & custom description)
  const handleActionClick = useCallback(async (
    actionType: ActionType,
    targetNpc: string,
    item: string | null,
    description?: string
  ) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.performAction(actionType, targetNpc, item || undefined, description);
      setGameState(res.updated_state);
      
      // Target NPC's immediate reaction
      const reaction = res.npc_reactions[targetNpc];
      if (reaction) {
        setDialogue({
          npc: targetNpc,
          text: reaction,
          provenance: [],
          mode: 'hybrid'
        });
      }
      setClassification(null);
    } catch (e: any) {
      setError(`Action failed: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Classify and perform a custom action
  const handleCustomActionClick = useCallback(async (description: string, item: string | null) => {
    setLoading(true);
    setError(null);
    try {
      // 1. Vector classify description
      const classificationResult = await api.classifyAction(description);
      setClassification(classificationResult);

      // 2. Perform the action if classification confidence is sufficient (>0.3)
      if (classificationResult.confidence >= 0.3) {
        const target = Object.values(gameState?.npcs || {}).find(
          n => n.location === playerLocation
        )?.name || Object.keys(gameState?.npcs || {})[0] || '';

        if (!target) {
          throw new Error('No target NPC found at your location.');
        }

        // Map valence/action_type to valid ActionType enum
        let finalActionType: ActionType = 'ask_rumor';
        const rawActionType = classificationResult.action_type;

        const validActions = ['steal', 'gift', 'help', 'lie', 'apologize', 'threaten', 'ask_rumor', 'return_item'];
        if (rawActionType && rawActionType !== 'classified' && validActions.includes(rawActionType)) {
          finalActionType = rawActionType as ActionType;
        } else {
          if (classificationResult.valence === 'positive') {
            finalActionType = 'help';
          } else if (classificationResult.valence === 'negative') {
            finalActionType = 'threaten';
          }
        }

        const res = await api.performAction(finalActionType, target, item || undefined, description);
        setGameState(res.updated_state);

        // Show dialogue
        const reaction = res.npc_reactions[target];
        if (reaction) {
          setDialogue({
            npc: target,
            text: reaction,
            provenance: [],
            mode: 'hybrid',
          });
        }
      } else {
        setError(`Classification confidence too low (${(classificationResult.confidence * 100).toFixed(0)}%). Action not performed.`);
      }
    } catch (e: any) {
      setError(`Custom Action failed: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  }, [gameState, playerLocation]);

  // Talk to a specific NPC (triggers Cognee Cloud query in active mode)
  const talkToNpc = useCallback(async (npcName: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDialogue(npcName, mode);
      setDialogue({
        npc: npcName,
        text: res.dialogue,
        provenance: res.provenance,
        mode: res.mode,
      });
    } catch (e: any) {
      setError(`Dialogue recall failed: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  }, [mode]);

  // Open baseline side-by-side comparison overlay
  const handleCompareBaselines = useCallback(() => {
    const activeNpc = dialogue?.npc || Object.keys(gameState?.npcs || {})[0] || 'Mira';
    setCompareNpcName(activeNpc);
    setIsCompareOpen(true);
  }, [dialogue, gameState]);

  // Reset session
  const resetGame = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.resetSession();
      setGameState(res.state);
      setPlayerLocation(res.state.player_location);
      setDialogue(null);
      setClassification(null);
    } catch (e: any) {
      setError(`Reset failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  if (!gameState || !mergedGameState) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4">
        <div className="text-indigo-400 text-3xl font-extrabold tracking-wider animate-pulse">ECHO</div>
        <div className="text-slate-500 text-sm">Connecting to Cognee Cloud memory substrate...</div>
      </div>
    );
  }

  // Faction card color classes
  const FACTION_BORDER_COLORS: Record<string, string> = {
    'Orchard Guild': 'border-green-500/30 hover:border-green-500/50 bg-green-950/5',
    'Shrine Circle': 'border-purple-500/30 hover:border-purple-500/50 bg-purple-950/5',
    'Alley Network': 'border-amber-500/30 hover:border-amber-500/50 bg-amber-950/5',
  };

  const FACTION_BADGES: Record<string, string> = {
    'Orchard Guild': 'bg-green-500/10 text-green-400 border-green-500/20',
    'Shrine Circle': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    'Alley Network': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col">
      {/* Top Header Bar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between shadow-lg z-10 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-black tracking-widest bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">ECHO</h1>
          <span className="text-[10px] text-indigo-300 font-bold bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 rounded-full uppercase tracking-wider">
            Cognee Cloud Memory Simulation
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* Mode Switcher */}
          <div className="flex items-center gap-2 bg-slate-950 rounded-lg p-1 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 px-2">Recall Mode:</span>
            {(['graph', 'vector', 'hybrid'] as MemoryMode[]).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-3 py-1 text-[10px] rounded font-bold uppercase transition cursor-pointer select-none ${
                  mode === m
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <button
            onClick={resetGame}
            disabled={loading}
            className="text-[10px] font-bold text-slate-400 hover:text-white bg-slate-800 border border-slate-700 px-3 py-2 rounded-lg transition hover:bg-slate-700 cursor-pointer disabled:opacity-50 select-none"
          >
            RESET WORLD
          </button>
        </div>
      </header>

      {/* Error Banners */}
      {error && (
        <div className="bg-red-950/40 border-b border-red-800/50 px-6 py-2.5 text-xs text-red-200 flex justify-between items-center animate-fade-in shrink-0">
          <div className="flex items-center gap-2">
            <span className="bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center font-bold text-[10px]">!</span>
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 font-bold px-2 cursor-pointer">✕</button>
        </div>
      )}

      {/* Main Grid View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side Game Board */}
        <div className="flex-1 p-6 space-y-4 overflow-y-auto">
          {/* Quick travel buttons */}
          <LocationBar currentLocation={playerLocation} onMoveTo={setPlayerLocation} />

          {/* Map canvas */}
          <div className="flex flex-col space-y-2">
            <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">
              2D Village Map (Lumen Market)
            </div>
            <div className="text-[10px] text-slate-500 font-medium">
              * Clicking a location marker directly on the map travels there. Clicking an NPC dot talks to them.
            </div>
            <GameCanvas
              gameState={mergedGameState}
              onNpcClick={talkToNpc}
              onLocationClick={setPlayerLocation}
            />
          </div>

          {/* Actions & Custom Text Actions */}
          <ActionPanel
            gameState={mergedGameState}
            loading={loading}
            onActionClick={handleActionClick}
            onCustomActionClick={handleCustomActionClick}
            classification={classification}
            onClearClassification={() => setClassification(null)}
          />

          {/* NPC Cards */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                NPC Quick-List (Click Card to Talk)
              </h3>
              <button
                onClick={handleCompareBaselines}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 underline font-bold cursor-pointer select-none active:scale-95 transition"
              >
                📊 Compare Baselines for dialogue
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(mergedGameState.npcs).map(([name, npc]) => {
                const borderClass = npc.faction ? FACTION_BORDER_COLORS[npc.faction] || 'border-slate-800 hover:border-slate-700 bg-slate-900/40' : 'border-slate-800 hover:border-slate-700 bg-slate-900/40';
                const badgeClass = npc.faction ? FACTION_BADGES[npc.faction] || 'bg-slate-800 text-slate-400 border-slate-700' : 'bg-slate-800 text-slate-400 border-slate-700';

                return (
                  <button
                    key={name}
                    onClick={() => talkToNpc(name)}
                    disabled={loading}
                    className={`border rounded-xl p-3.5 text-left transition transform hover:-translate-y-0.5 hover:shadow-lg flex flex-col justify-between cursor-pointer disabled:opacity-50 select-none ${borderClass}`}
                  >
                    <div className="w-full">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-extrabold text-sm text-slate-100">{name}</span>
                        <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded border uppercase ${badgeClass}`}>
                          {npc.faction || 'Factionless'}
                        </span>
                      </div>
                      
                      <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1 mb-2.5">
                        <svg className="w-3 h-3 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {npc.location.replace('_', ' ')}
                      </div>
                    </div>

                    {/* NPC Status meters */}
                    <div className="grid grid-cols-4 gap-1 text-[9px] font-mono border-t border-slate-800/50 pt-2.5 mt-1 w-full text-slate-500">
                      <div className="flex flex-col">
                        <span>TRU</span>
                        <span className="text-green-400 font-bold">{npc.trust}</span>
                      </div>
                      <div className="flex flex-col">
                        <span>ANG</span>
                        <span className="text-red-400 font-bold">{npc.anger}</span>
                      </div>
                      <div className="flex flex-col">
                        <span>FEA</span>
                        <span className="text-yellow-400 font-bold">{npc.fear}</span>
                      </div>
                      <div className="flex flex-col">
                        <span>RES</span>
                        <span className="text-blue-400 font-bold">{npc.respect}</span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dialogue Box display */}
          <DialogueBox dialogue={dialogue} gameState={mergedGameState} />

          {/* Processing memory tag */}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-slate-500 py-1.5 px-3 bg-slate-900 border border-slate-800 rounded-lg w-max animate-pulse">
              <div className="w-2 h-2 bg-indigo-500 rounded-full animate-ping"></div>
              <span>Processing Memory Sync...</span>
            </div>
          )}
        </div>

        {/* Right Side Tab Inspector */}
        <div className="w-80 border-l border-slate-800 flex-shrink-0">
          <InspectorPanel
            gameState={mergedGameState}
            mode={mode}
            onCompareBaselines={handleCompareBaselines}
          />
        </div>
      </div>

      {/* Side-by-Side Dialogue Mode Comparison Modal Overlay */}
      <BaselineComparison
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        npcName={compareNpcName}
      />
    </div>
  );
}
