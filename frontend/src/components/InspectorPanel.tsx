import { useState, useEffect } from 'react';
import type { GameState, MemoryMode, MemoryGraph, BeliefRecord, FactionMood } from '../types';
import * as api from '../api';
import { GraphAnimation } from './GraphAnimation';

interface Props {
  gameState: GameState;
  mode: MemoryMode;
  onCompareBaselines: () => void;
}

type Tab = 'graph' | 'facts' | 'beliefs' | 'factions' | 'baseline';

export function InspectorPanel({ gameState, mode, onCompareBaselines }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('graph');
  const [graph, setGraph] = useState<MemoryGraph | null>(null);
  const [beliefs, setBeliefs] = useState<Record<string, BeliefRecord[]>>({});
  const [factions, setFactions] = useState<Record<string, FactionMood>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const p1 = api.fetchMemoryGraph().then(setGraph).catch(() => {});
    const p2 = api.fetchBeliefs().then(setBeliefs).catch(() => {});
    const p3 = api.fetchFactions().then(setFactions).catch(() => {});
    Promise.all([p1, p2, p3]).finally(() => setLoading(false));
  }, [gameState]);

  const tabs: { key: Tab; label: string }[] = [
    { key: 'graph', label: 'Graph' },
    { key: 'facts', label: 'Facts' },
    { key: 'beliefs', label: 'Beliefs' },
    { key: 'factions', label: 'Factions' },
    { key: 'baseline', label: 'Baseline' },
  ];

  return (
    <div className="h-full flex flex-col p-4 bg-slate-900 border-l border-slate-800 text-slate-200">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Memory Inspector
        </h2>
        {loading && (
          <div className="flex space-x-1">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-slate-950/80 rounded-lg p-1 border border-slate-800">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 text-[10px] font-bold uppercase py-1.5 rounded transition cursor-pointer select-none ${
              activeTab === tab.key
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content Area */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2 text-xs">
        {activeTab === 'graph' && <GraphTab graph={graph} />}
        {activeTab === 'facts' && <FactsTab events={gameState.recent_events} />}
        {activeTab === 'beliefs' && <BeliefsTab beliefs={beliefs} />}
        {activeTab === 'factions' && <FactionsTab factions={factions} />}
        {activeTab === 'baseline' && <BaselineTab mode={mode} onCompare={onCompareBaselines} />}
      </div>
    </div>
  );
}

function GraphTab({ graph }: { graph: MemoryGraph | null }) {
  return <GraphAnimation graph={graph} />;
}

function FactsTab({ events }: { events: any[] }) {
  if (events.length === 0) {
    return (
      <div className="text-slate-600 italic py-4 text-center">
        No events recorded yet.<br />Steal or gift something to start.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {[...events].reverse().map((ev, i) => (
        <div key={i} className="bg-slate-950/80 border border-slate-800 rounded-lg p-2.5 space-y-1 animate-fade-in">
          <div className="flex justify-between items-center border-b border-slate-900 pb-1">
            <span className="font-bold text-indigo-400 capitalize">{ev.action_type}</span>
            <span className="text-[8px] font-mono text-slate-600">ID: {ev.event_id.replace('evt_', '')}</span>
          </div>
          <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-slate-400 text-[10px]">
            <div>Actor: <span className="text-slate-200">Player</span></div>
            <div>Target: <span className="text-slate-200">{ev.target_npc}</span></div>
            {ev.item && <div className="col-span-2">Item: <span className="text-emerald-400">{ev.item}</span></div>}
            <div className="col-span-2 text-slate-500 truncate">
              Witnesses: <span className="text-slate-300">{ev.witnesses.join(', ') || 'none'}</span>
            </div>
          </div>
          <div className="text-[8px] text-slate-600 text-right mt-1">
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
    return (
      <div className="text-slate-600 italic py-4 text-center">
        No NPC beliefs yet.<br />Memory hasn't propagated to local records.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {Object.entries(beliefs).map(([npc, npcBeliefs]) =>
        npcBeliefs.map((b, i) => {
          const cert = b.certainty;
          const certaintyPct = (cert * 100).toFixed(0);
          
          let certaintyColor = 'text-red-400';
          let barBgColor = 'bg-red-500';
          if (cert > 0.7) {
            certaintyColor = 'text-green-400';
            barBgColor = 'bg-green-500';
          } else if (cert > 0.3) {
            certaintyColor = 'text-yellow-400';
            barBgColor = 'bg-yellow-500';
          }

          return (
            <div key={`${npc}-${i}`} className="bg-slate-950/80 border border-slate-800 rounded-lg p-2.5 animate-fade-in space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-200">{npc}</span>
                <span className={`text-[10px] font-bold ${certaintyColor}`}>
                  {certaintyPct}% Certain
                </span>
              </div>
              
              {/* Certainty Bar */}
              <div className="w-full bg-slate-900 rounded-full h-1.5 mt-0.5">
                <div
                  className={`${barBgColor} h-1.5 rounded-full transition-all duration-500`}
                  style={{ width: `${certaintyPct}%` }}
                />
              </div>

              <div className="text-slate-400 text-[10px] pt-1">
                Event: <span className="font-mono text-indigo-400">{b.event_id.replace('evt_', '')}</span>
              </div>
              <div className="text-[10px] text-slate-500 flex justify-between items-center pt-0.5 border-t border-slate-900">
                <span>Source: <strong className="text-slate-400">{b.source}</strong></span>
                {b.heard_from && (
                  <span>via <strong className="text-slate-400">{b.heard_from}</strong></span>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

function FactionsTab({ factions }: { factions: Record<string, FactionMood> }) {
  const entries = Object.entries(factions);
  if (entries.length === 0) {
    return <div className="text-slate-600 italic py-4 text-center">Loading faction sentiment...</div>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([name, mood]) => (
        <div key={name} className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 animate-fade-in">
          <h4 className="font-bold text-xs mb-2 text-indigo-400 border-b border-slate-900 pb-1">{name}</h4>
          <div className="space-y-2">
            <MeterBar label="Trust" value={mood.trust} color="from-green-600 to-green-400" />
            <MeterBar label="Fear" value={mood.fear} color="from-yellow-600 to-yellow-400" />
            <MeterBar label="Respect" value={mood.respect} color="from-blue-600 to-blue-400" />
            <MeterBar label="Anger" value={mood.anger} color="from-red-600 to-red-400" />
          </div>
          {mood.last_event && (
            <div className="text-[9px] text-slate-600 mt-2 border-t border-slate-900 pt-1.5 flex justify-between">
              <span>Last Event:</span>
              <span className="font-mono text-slate-400">{mood.last_event}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function MeterBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-400 w-11">{label}</span>
      <div className="flex-1 bg-slate-750 rounded-full h-3 overflow-hidden border border-slate-800">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r ${color}`}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
      <span className="text-[10px] text-slate-450 w-6 text-right font-mono">{value.toFixed(0)}</span>
    </div>
  );
}

function BaselineTab({ mode, onCompare }: { mode: MemoryMode; onCompare: () => void }) {
  const comparisons = [
    {
      mode: 'graph' as MemoryMode,
      strength: 'Tracks exact facts: who saw what, who knows whom.',
      weakness: 'Cannot generalize meaning. Treats "stole relic" and "betrayed trust" as separate facts.',
      example: 'Rowan knows theft_001 happened but responds mechanically without emotion.',
    },
    {
      mode: 'vector' as MemoryMode,
      strength: 'Generalizes emotional meaning across similar events.',
      weakness: 'Cannot enforce knowledge boundaries. May leak facts to uninformed NPCs.',
      example: 'Sol, who was never told, might say "I heard about the theft..." because of vector similarity.',
    },
    {
      mode: 'hybrid' as MemoryMode,
      strength: 'Grounded facts + emotional intelligence. Partial knowledge boundaries are strictly enforced.',
      weakness: 'Slightly slower than pure vector recall (but still sub-second).',
      example: 'Rowan knows through Mira (ally); Sol does not know unless told.',
    },
  ];

  return (
    <div className="space-y-3">
      <button
        onClick={onCompare}
        className="w-full bg-indigo-700 hover:bg-indigo-600 text-white font-extrabold py-2 px-3 rounded-lg text-xs transition cursor-pointer shadow-md flex items-center justify-center gap-1.5 mb-2 select-none active:scale-95 border border-indigo-600"
      >
        📊 Compare All Modes Side-by-Side
      </button>
      {comparisons.map(c => (
        <div
          key={c.mode}
          className={`bg-slate-950/80 border rounded-xl p-3 transition-all duration-300 ${
            mode === c.mode
              ? 'border-indigo-500 ring-1 ring-indigo-500/30'
              : 'border-slate-800'
          }`}
        >
          <div className="flex items-center gap-2 mb-1.5">
            <span className={`text-xs font-bold uppercase tracking-wider ${
              mode === c.mode ? 'text-indigo-400' : 'text-slate-400'
            }`}>
              {c.mode}
            </span>
            {mode === c.mode && (
              <span className="text-[8px] font-bold bg-indigo-600 text-white px-1.5 py-0.5 rounded">ACTIVE</span>
            )}
          </div>
          <div className="space-y-1.5 text-[10px] leading-relaxed">
            <div className="text-green-400/90 font-medium">✓ {c.strength}</div>
            <div className="text-red-400/90 font-medium">✗ {c.weakness}</div>
            <div className="text-slate-500 italic pt-1 border-t border-slate-900">Ex: {c.example}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
