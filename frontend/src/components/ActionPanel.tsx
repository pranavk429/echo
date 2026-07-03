import { useState } from 'react';
import type { ActionType, GameState } from '../types';

interface ActionConfig {
  type: ActionType;
  label: string;
  colorClass: string;
}

const ACTIONS: ActionConfig[] = [
  { type: 'steal', label: 'Steal', colorClass: 'bg-[#dc2626] hover:bg-[#b91c1c] text-white' },
  { type: 'gift', label: 'Gift', colorClass: 'bg-[#22c55e] hover:bg-[#16a34a] text-white' },
  { type: 'help', label: 'Help', colorClass: 'bg-[#10b981] hover:bg-[#059669] text-white' }, // NOTE: help action type is "help"
  { type: 'lie', label: 'Lie', colorClass: 'bg-[#eab308] hover:bg-[#ca8a04] text-white' },
  { type: 'apologize', label: 'Apologize', colorClass: 'bg-[#3b82f6] hover:bg-[#2563eb] text-white' },
  { type: 'threaten', label: 'Threaten', colorClass: 'bg-[#f97316] hover:bg-[#ea580c] text-white' },
  { type: 'ask_rumor', label: 'Ask Rumor', colorClass: 'bg-[#a855f7] hover:bg-[#9333ea] text-white' },
  { type: 'return_item', label: 'Return Item', colorClass: 'bg-[#14b8a6] hover:bg-[#0d9488] text-white' },
];

const ITEMS = [
  { id: 'relic', label: 'Guild Relic', emoji: '🏺' },
  { id: 'apple', label: 'Apple', emoji: '🍎' },
  { id: 'coin', label: 'Gold Coin', emoji: '🪙' },
  { id: 'flower', label: 'Lumen Flower', emoji: '🌸' },
  { id: 'letter', label: 'Sealed Letter', emoji: '✉️' },
  { id: null, label: 'No Item', emoji: '—' },
];

interface Props {
  gameState: GameState;
  loading: boolean;
  onActionClick: (actionType: ActionType, targetNpc: string, item: string | null, description?: string) => void;
  onCustomActionClick: (description: string, item: string | null) => void;
  classification: any;
  onClearClassification: () => void;
}

export function ActionPanel({
  gameState,
  loading,
  onActionClick,
  onCustomActionClick,
  classification,
  onClearClassification,
}: Props) {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [customAction, setCustomAction] = useState('');

  // Find target: first NPC at player's location, or first NPC overall
  const targetNpc = Object.values(gameState.npcs).find(
    n => n.location === gameState.player_location
  )?.name || Object.keys(gameState.npcs)[0] || '';

  const handleAction = (type: ActionType) => {
    if (!targetNpc) return;
    onActionClick(type, targetNpc, selectedItem, customAction.trim() || undefined);
    setCustomAction('');
  };

  const handleCustomActionPerform = () => {
    if (!customAction.trim()) return;
    onCustomActionClick(customAction.trim(), selectedItem);
    setCustomAction('');
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
      {/* Target Status bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider">
          Actions
        </h3>
        {targetNpc && (
          <span className="text-xs text-slate-500">
            Targeting: <strong className="text-indigo-400">{targetNpc}</strong> at{' '}
            <span className="italic">{gameState.player_location.replace('_', ' ')}</span>
          </span>
        )}
      </div>

      {/* Grid of Action Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {ACTIONS.map(action => (
          <button
            key={action.type}
            onClick={() => handleAction(action.type)}
            disabled={loading || !targetNpc}
            className={`px-3 py-2.5 rounded-lg text-xs font-bold transition transform active:scale-95 disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex flex-col items-center justify-center gap-0.5 shadow-md ${action.colorClass}`}
          >
            <span>{action.label}</span>
            {targetNpc && (
              <span className="text-[9px] opacity-75 font-normal">
                {action.type === 'ask_rumor' ? `about ${targetNpc}` : `on ${targetNpc}`}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Item Picker */}
      <div className="space-y-1.5 pt-1 border-t border-slate-850">
        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
          Select Item to Use
        </div>
        <div className="flex flex-wrap gap-1.5">
          {ITEMS.map(item => {
            const isSelected = selectedItem === item.id;
            return (
              <button
                key={item.id ?? 'no_item'}
                onClick={() => setSelectedItem(item.id)}
                className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold border transition cursor-pointer select-none flex items-center gap-1 ${
                  isSelected
                    ? 'bg-indigo-650 border-indigo-500 text-white shadow-sm'
                    : 'bg-slate-950 border-slate-850 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <span>{item.emoji}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Open Action Input Box (Anti-Hardcode Proof) */}
      <div className="space-y-2 pt-2 border-t border-slate-850">
        <div className="flex justify-between items-center">
          <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            Custom Action (Anti-Hardcode Proof)
          </div>
          {classification && (
            <button
              onClick={onClearClassification}
              className="text-[9px] text-slate-500 hover:text-slate-350 underline cursor-pointer select-none"
            >
              Clear Result
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type any custom action... (e.g. 'I threatened Niko with a knife')"
            className="flex-1 bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-650 focus:outline-none focus:border-indigo-500/50 transition"
            value={customAction}
            onChange={e => setCustomAction(e.target.value)}
            disabled={loading}
          />
          <button
            onClick={handleCustomActionPerform}
            disabled={loading || !customAction.trim() || !targetNpc}
            className="bg-indigo-700 hover:bg-indigo-600 text-white text-xs font-bold px-4 py-2 rounded-lg transition disabled:opacity-50 cursor-pointer shadow-md select-none shrink-0"
          >
            Perform Custom Action
          </button>
        </div>

        {/* Display Classification Result if present */}
        {classification && (
          <div className="bg-slate-950/80 border border-slate-850 rounded-lg p-2.5 text-xs space-y-1.5 animate-fade-in">
            <div className="flex justify-between items-center border-b border-slate-900 pb-1">
              <span className="font-semibold text-slate-400">Cognee Vector Classification</span>
              <span className="text-[9px] text-slate-500">Confidence: {(classification.confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <div>Valence: <span className={`font-bold uppercase ${
                classification.valence === 'negative' ? 'text-red-400' :
                classification.valence === 'positive' ? 'text-green-400' : 'text-yellow-400'
              }`}>{classification.valence}</span></div>
              <div>Classified Action: <span className="font-bold text-indigo-400 uppercase">{classification.action_type}</span></div>
            </div>
            <div className="text-[9px] text-slate-550 font-mono leading-normal pt-1 border-t border-slate-900 break-words">
              LLM Raw: "{classification.raw}"
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
