import type { Detection } from "../types";

interface DetectionPanelProps {
  detections: Detection[];
  fps: number;
  inferenceMs: number;
}

export function DetectionPanel({ detections, fps, inferenceMs }: DetectionPanelProps) {
  // Count by class
  const counts: Record<string, number> = {};
  for (const d of detections) {
    counts[d.class] = (counts[d.class] || 0) + 1;
  }

  return (
    <div className="bg-surface-raised rounded-lg border border-surface-overlay p-4 min-w-[200px]">
      <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
        Detections
      </h3>

      {/* Performance */}
      <div className="flex gap-4 mb-3 text-xs font-mono">
        <div>
          <span className="text-gray-500">FPS </span>
          <span className="text-accent-glow">{fps.toFixed(1)}</span>
        </div>
        <div>
          <span className="text-gray-500">Infer </span>
          <span className="text-accent-glow">{inferenceMs.toFixed(1)}ms</span>
        </div>
      </div>

      {/* Object count list */}
      {Object.entries(counts).length > 0 ? (
        <ul className="space-y-1">
          {Object.entries(counts)
            .sort(([, a], [, b]) => b - a)
            .map(([className, count]) => (
              <li
                key={className}
                className="flex justify-between text-xs font-mono"
              >
                <span className="text-gray-300">{className}</span>
                <span className="text-gray-500">×{count}</span>
              </li>
            ))}
        </ul>
      ) : (
        <p className="text-xs text-gray-600 font-mono italic">
          No objects detected
        </p>
      )}
    </div>
  );
}
