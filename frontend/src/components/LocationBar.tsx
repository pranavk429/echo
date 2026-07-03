import type { Location } from '../types';

const LOCATIONS: { id: Location; label: string; emoji: string }[] = [
  { id: 'town_square', label: 'Town Square', emoji: '🏛️' },
  { id: 'orchard_stall', label: 'Orchard Stall', emoji: '🍎' },
  { id: 'guild_hall', label: 'Guild Hall', emoji: '🛡️' },
  { id: 'shrine', label: 'Shrine', emoji: '🔮' },
  { id: 'alley', label: 'Alley', emoji: '🏚️' },
];

interface Props {
  currentLocation: Location;
  onMoveTo: (location: Location) => void;
}

export function LocationBar({ currentLocation, onMoveTo }: Props) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2">
      <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
        Quick Travel Locations
      </div>
      <div className="flex flex-wrap gap-1.5">
        {LOCATIONS.map(loc => {
          const isActive = currentLocation === loc.id;
          return (
            <button
              key={loc.id}
              onClick={() => onMoveTo(loc.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer border select-none ${
                isActive
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-950 border-slate-850 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <span>{loc.emoji}</span>
              <span>{loc.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
