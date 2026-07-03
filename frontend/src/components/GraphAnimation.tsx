import type { MemoryGraph } from '../types';

interface Props {
  graph: MemoryGraph | null;
}

export function GraphAnimation({ graph }: Props) {
  if (!graph) return <div className="text-slate-600 italic">Loading memory graph...</div>;
  if (graph.edges.length === 0) {
    return (
      <div className="text-slate-600 italic py-4 text-center">
        No memory edges yet.<br />Perform an action to populate memory.
      </div>
    );
  }

  // Show up to the last 15 edges, newest first
  const recentEdges = graph.edges.slice(-15).reverse();
  const totalCount = graph.edges.length;

  return (
    <div className="space-y-2">
      <div className="text-slate-500 text-[10px] font-mono flex justify-between border-b border-slate-850 pb-1 mb-2">
        <span>{graph.nodes.length} nodes · {totalCount} edges</span>
        <span className="text-[9px] text-indigo-400 font-semibold animate-pulse">PROPAGATING WALK</span>
      </div>

      <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
        {recentEdges.map((edge, i) => {
          // Staggered entry delay
          const delay = `${i * 100}ms`;
          // Pulse the 3 most recent edges
          const isPulsing = i < 3;

          return (
            <div
              key={`${edge.source}-${edge.target}-${edge.label}-${i}`}
              className={`text-[10px] font-mono bg-slate-950/90 px-3 py-2 rounded-lg border transition-all duration-300 flex flex-col gap-1.5 ${
                isPulsing
                  ? 'border-indigo-500/60 shadow-md shadow-indigo-500/5 edge-pulse'
                  : 'border-slate-850'
              }`}
              style={{ animationDelay: delay }}
            >
              <div className="flex justify-between items-center text-[8px] text-slate-600 select-none">
                <span>HOP {totalCount - i}</span>
                {isPulsing && (
                  <span className="flex items-center gap-1">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-indigo-500"></span>
                    </span>
                    <span className="text-indigo-400/80 font-bold uppercase tracking-wider text-[7px]">PULSING</span>
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1 select-text">
                <span className="text-blue-400 font-extrabold">{edge.source}</span>
                <span className="text-slate-600">──[</span>
                <span className="text-slate-400 font-semibold bg-slate-900/60 px-1 py-0.5 rounded border border-slate-800/80 text-[8px]">
                  {edge.label}
                </span>
                <span className="text-slate-600">]──→</span>
                <span className="text-green-400 font-extrabold">{edge.target}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
