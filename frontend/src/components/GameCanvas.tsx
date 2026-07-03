import { useRef, useEffect, useMemo } from 'react';
import type { Location, GameState } from '../types';

// Pixel positions for each location on the map
const LOCATION_COORDS: Record<Location, { x: number; y: number }> = {
  orchard_stall: { x: 150, y: 100 },
  guild_hall:    { x: 400, y: 80 },
  shrine:        { x: 300, y: 250 },
  alley:         { x: 100, y: 200 },
  town_square:   { x: 250, y: 150 },
};

const LOCATION_NAMES: Record<Location, string> = {
  orchard_stall: 'Orchard Stall',
  guild_hall: 'Guild Hall',
  shrine: 'Shrine',
  alley: 'Alley',
  town_square: 'Town Square',
};

const FACTION_COLORS: Record<string, string> = {
  'Orchard Guild': '#22c55e',    // green
  'Shrine Circle': '#a855f7',    // purple
  'Alley Network': '#f59e0b',    // amber
};

const DEFAULT_NPC_COLOR = '#6b7280'; // gray for factionless NPCs

interface Props {
  gameState: GameState;
  onNpcClick: (npcName: string) => void;
  onLocationClick: (location: Location) => void;
}

export function GameCanvas({ gameState, onNpcClick, onLocationClick }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Group all entities (player + NPCs) by location for rendering and clicking
  const entitiesByLocation = useMemo(() => {
    const map: Record<string, { type: 'player' | 'npc'; name: string }[]> = {};
    
    // Add player
    if (gameState.player_location) {
      map[gameState.player_location] = [
        { type: 'player', name: 'You' }
      ];
    }
    
    // Add NPCs
    for (const [name, npc] of Object.entries(gameState.npcs)) {
      if (!map[npc.location]) {
        map[npc.location] = [];
      }
      map[npc.location].push({ type: 'npc', name });
    }
    
    return map;
  }, [gameState]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = 500;
    const H = 350;
    canvas.width = W;
    canvas.height = H;

    // Clear background
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, W, H);

    // Draw paths/roads (slate-600)
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 3;
    const center = LOCATION_COORDS.town_square;
    for (const loc of Object.keys(LOCATION_COORDS) as Location[]) {
      if (loc === 'town_square') continue;
      const pos = LOCATION_COORDS[loc];
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
    }

    // Draw location markers (gray circles)
    for (const [loc, pos] of Object.entries(LOCATION_COORDS)) {
      const isSquare = loc === 'town_square';
      ctx.fillStyle = '#334155';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isSquare ? 22 : 18, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Location name
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(LOCATION_NAMES[loc as Location], pos.x, pos.y + (isSquare ? 34 : 30));
    }

    // Draw entities (player + NPCs) with offset placement if clustered
    for (const [loc, entities] of Object.entries(entitiesByLocation)) {
      const pos = LOCATION_COORDS[loc as Location];
      if (!pos) continue;

      entities.forEach((entity, index) => {
        let offsetX = 0;
        let offsetY = 0;
        if (entities.length > 1) {
          const angle = (index * 2 * Math.PI) / entities.length;
          offsetX = Math.cos(angle) * 16;
          offsetY = Math.sin(angle) * 16;
        }
        const x = pos.x + offsetX;
        const y = pos.y + offsetY;

        if (entity.type === 'player') {
          // Draw Player dot
          ctx.fillStyle = '#60a5fa'; // Blue
          ctx.beginPath();
          ctx.arc(x, y, 9, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Draw label
          ctx.fillStyle = '#60a5fa';
          ctx.font = 'bold 9px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('You', x, y - 14);
        } else {
          // Draw NPC dot
          const npc = gameState.npcs[entity.name];
          const color = npc.faction ? FACTION_COLORS[npc.faction] || DEFAULT_NPC_COLOR : DEFAULT_NPC_COLOR;

          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(x, y, 8, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Draw label
          ctx.fillStyle = '#e2e8f0';
          ctx.font = 'bold 9px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(entity.name, x, y - 13);

          // Clickable indicator
          ctx.fillStyle = '#64748b';
          ctx.font = '8px sans-serif';
          ctx.fillText('(click)', x, y + 15);
        }
      });
    }

  }, [gameState, entitiesByLocation]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    // Check if click is near an NPC
    for (const [name, npc] of Object.entries(gameState.npcs)) {
      const pos = LOCATION_COORDS[npc.location];
      const entities = entitiesByLocation[npc.location] || [];
      const index = entities.findIndex(ent => ent.type === 'npc' && ent.name === name);
      
      let offsetX = 0;
      let offsetY = 0;
      if (entities.length > 1 && index !== -1) {
        const angle = (index * 2 * Math.PI) / entities.length;
        offsetX = Math.cos(angle) * 16;
        offsetY = Math.sin(angle) * 16;
      }
      
      const npcX = pos.x + offsetX;
      const npcY = pos.y + offsetY;
      const dist = Math.sqrt((x - npcX) ** 2 + (y - npcY) ** 2);
      if (dist < 18) {
        onNpcClick(name);
        return;
      }
    }

    // Check if click is near a location marker
    for (const [loc, pos] of Object.entries(LOCATION_COORDS)) {
      const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (dist < 24) {
        onLocationClick(loc as Location);
        return;
      }
    }
  };

  return (
    <div className="flex justify-center w-full">
      <canvas
        ref={canvasRef}
        onClick={handleClick}
        className="rounded-lg border border-slate-800 cursor-pointer w-full max-w-[500px]"
        style={{ height: '350px' }}
      />
    </div>
  );
}
