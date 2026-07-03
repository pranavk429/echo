import type { GameState, MemoryMode } from '../types';

interface Props {
  dialogue: {
    npc: string;
    text: string;
    provenance: any[];
    mode: MemoryMode;
  } | null;
  gameState: GameState;
}

const FACTION_TEXT_COLORS: Record<string, string> = {
  'Orchard Guild': 'text-green-400',
  'Shrine Circle': 'text-purple-400',
  'Alley Network': 'text-amber-400',
};

const NPC_ROLES: Record<string, string> = {
  Mira: 'orchard merchant',
  Rowan: 'guild guard',
  Sol: 'shrine keeper',
  Niko: 'alley broker',
  Vale: 'town crier',
  Ilya: 'outsider traveler',
};

export function DialogueBox({ dialogue, gameState }: Props) {
  if (!dialogue) return null;

  const npcState = gameState.npcs[dialogue.npc];
  const faction = npcState?.faction;
  const colorClass = faction ? FACTION_TEXT_COLORS[faction] || 'text-slate-300' : 'text-slate-300';
  const role = NPC_ROLES[dialogue.npc] || '';

  return (
    <div className="bg-indigo-950/20 border border-indigo-500/30 rounded-xl p-4 space-y-3 animate-fade-in">
      <div className="flex items-center justify-between border-b border-indigo-500/10 pb-2">
        <div className="flex items-center gap-2">
          <span className={`text-base font-bold ${colorClass}`}>
            {dialogue.npc}
          </span>
          {role && (
            <span className="text-xs text-indigo-300/60 font-medium">
              ({role})
            </span>
          )}
          {faction && (
            <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded-full border border-slate-700">
              {faction}
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded">
          {dialogue.mode} mode
        </span>
      </div>

      <div className="text-indigo-100 text-sm leading-relaxed whitespace-pre-line italic">
        "{dialogue.text}"
      </div>

      {dialogue.provenance && dialogue.provenance.length > 0 && (
        <details className="text-xs text-indigo-300/70 select-none group border-t border-indigo-500/10 pt-2 mt-1">
          <summary className="cursor-pointer hover:text-indigo-200 transition flex items-center gap-1 font-semibold">
            <svg
              className="w-3.5 h-3.5 transform transition-transform group-open:rotate-90 text-indigo-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M9 5l7 7-7 7"
              />
            </svg>
            What influenced this response? (Provenance)
          </summary>
          <div className="mt-2 overflow-x-auto max-h-48 bg-slate-950/80 border border-indigo-500/10 p-3 rounded-lg font-mono text-[10px] text-slate-400 leading-normal">
            <pre>{JSON.stringify(dialogue.provenance, null, 2)}</pre>
          </div>
        </details>
      )}
    </div>
  );
}
