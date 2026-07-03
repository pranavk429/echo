import { useState, useEffect } from 'react';
import type { DialogueResponse } from '../types';
import * as api from '../api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  npcName: string;
}

export function BaselineComparison({ isOpen, onClose, npcName }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    graph: DialogueResponse | null;
    vector: DialogueResponse | null;
    hybrid: DialogueResponse | null;
  }>({ graph: null, vector: null, hybrid: null });

  useEffect(() => {
    if (!isOpen || !npcName) return;

    setLoading(true);
    setError(null);
    setData({ graph: null, vector: null, hybrid: null });

    Promise.all([
      api.getDialogue(npcName, 'graph').catch(e => ({ npc_name: npcName, dialogue: `[Recall failed: ${e.message}]`, provenance: [], mode: 'graph' as const })),
      api.getDialogue(npcName, 'vector').catch(e => ({ npc_name: npcName, dialogue: `[Recall failed: ${e.message}]`, provenance: [], mode: 'vector' as const })),
      api.getDialogue(npcName, 'hybrid').catch(e => ({ npc_name: npcName, dialogue: `[Recall failed: ${e.message}]`, provenance: [], mode: 'hybrid' as const })),
    ])
      .then(([g, v, h]) => {
        setData({ graph: g as DialogueResponse, vector: v as DialogueResponse, hybrid: h as DialogueResponse });
      })
      .catch(e => {
        setError(`Failed to compare baselines: ${e.message}`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, npcName]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-[fadeIn_0.2s_ease-out]">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-fade-in">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-950 border-b border-slate-850 flex justify-between items-center">
          <div>
            <h2 className="text-base font-extrabold text-slate-100 flex items-center gap-2">
              <span>Baseline Mode Comparison</span>
              <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono">
                {npcName}
              </span>
            </h2>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Compare Cognee hybrid recall side-by-side with graph-only and vector-only search strategies.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer select-none"
          >
            ✕ Close
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {error && (
            <div className="bg-red-950/40 border border-red-800/40 px-4 py-2.5 rounded-lg text-xs text-red-200">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              <div className="text-slate-400 text-xs animate-pulse">Invoking Cognee Cloud parallel recalls...</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Graph Column */}
              <div className="bg-slate-950/60 border border-blue-500/30 rounded-xl p-4 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-center border-b border-slate-900 pb-1.5">
                    <span className="text-xs font-black uppercase text-blue-400">Graph Mode</span>
                    <span className="text-[8px] font-bold bg-blue-500/10 text-blue-300 border border-blue-500/20 px-1.5 py-0.5 rounded">
                      Factual
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 italic leading-relaxed pt-2 min-h-[90px] whitespace-pre-wrap">
                    {data.graph ? `"${data.graph.dialogue}"` : 'No dialogue returned.'}
                  </div>
                </div>
                <div className="space-y-1.5 border-t border-slate-900 pt-2.5">
                  <span className="text-[9px] font-bold text-red-400 uppercase tracking-wider block">Verdict:</span>
                  <div className="text-[10px] text-slate-500 leading-normal">
                    Rigid, no generalization. Responds with raw database facts, lacking emotional or narrative connection.
                  </div>
                </div>
              </div>

              {/* Vector Column */}
              <div className="bg-slate-950/60 border border-amber-500/30 rounded-xl p-4 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-center border-b border-slate-900 pb-1.5">
                    <span className="text-xs font-black uppercase text-amber-400">Vector Mode</span>
                    <span className="text-[8px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 px-1.5 py-0.5 rounded">
                      Emotional
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 italic leading-relaxed pt-2 min-h-[90px] whitespace-pre-wrap">
                    {data.vector ? `"${data.vector.dialogue}"` : 'No dialogue returned.'}
                  </div>
                </div>
                <div className="space-y-1.5 border-t border-slate-900 pt-2.5">
                  <span className="text-[9px] font-bold text-red-400 uppercase tracking-wider block">Verdict:</span>
                  <div className="text-[10px] text-slate-500 leading-normal">
                    May hallucinate facts. Leaks global context (e.g. details other characters saw but this one never learned).
                  </div>
                </div>
              </div>

              {/* Hybrid Column */}
              <div className="bg-slate-950/60 border border-green-500/40 rounded-xl p-4 flex flex-col justify-between space-y-4 ring-1 ring-green-500/20">
                <div className="space-y-2">
                  <div className="flex justify-between items-center border-b border-slate-900 pb-1.5">
                    <span className="text-xs font-black uppercase text-green-400">Cognee Hybrid</span>
                    <span className="text-[8px] font-bold bg-green-500/10 text-green-300 border border-green-500/20 px-1.5 py-0.5 rounded">
                      Grounded + Nuanced
                    </span>
                  </div>
                  <div className="text-xs text-slate-200 font-medium italic leading-relaxed pt-2 min-h-[90px] whitespace-pre-wrap">
                    {data.hybrid ? `"${data.hybrid.dialogue}"` : 'No dialogue returned.'}
                  </div>
                </div>
                <div className="space-y-1.5 border-t border-slate-900 pt-2.5">
                  <span className="text-[9px] font-bold text-green-400 uppercase tracking-wider block">Verdict:</span>
                  <div className="text-[10px] text-slate-400 leading-normal">
                    Factual boundaries are preserved via the graph, while emotional sentiment and phrasing adapt dynamically.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
