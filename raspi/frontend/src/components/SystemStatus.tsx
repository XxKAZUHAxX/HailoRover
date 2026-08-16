import type { SystemHealth } from "../types";

interface SystemStatusProps {
  health: SystemHealth | null;
  onRefresh: () => void;
}

export function SystemStatus({ health, onRefresh }: SystemStatusProps) {
  if (!health) {
    return (
      <div className="bg-surface-raised rounded-lg border border-surface-overlay p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
            System
          </h3>
          <button
            onClick={onRefresh}
            className="text-xs text-accent hover:text-accent-glow transition-colors"
          >
            Refresh
          </button>
        </div>
        <p className="text-xs text-gray-600 font-mono">Server unreachable</p>
      </div>
    );
  }

  const tempColor =
    health.cpu_temp_c !== null && health.cpu_temp_c > 70
      ? "text-danger"
      : health.cpu_temp_c !== null && health.cpu_temp_c > 55
        ? "text-warning"
        : "text-success";

  const uptimeMins = Math.floor(health.uptime_seconds / 60);

  return (
    <div className="bg-surface-raised rounded-lg border border-surface-overlay p-4 min-w-[200px]">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
          System
        </h3>
        <button
          onClick={onRefresh}
          className="text-xs text-accent hover:text-accent-glow transition-colors"
        >
          Refresh
        </button>
      </div>

      <dl className="space-y-1 text-xs font-mono">
        <div className="flex justify-between">
          <dt className="text-gray-500">CPU Temp</dt>
          <dd className={tempColor}>
            {health.cpu_temp_c !== null ? `${health.cpu_temp_c.toFixed(1)}°C` : "—"}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">NPU Temp</dt>
          <dd className="text-gray-300">
            {health.npu_temp_c !== null ? `${health.npu_temp_c.toFixed(1)}°C` : "—"}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">Uptime</dt>
          <dd className="text-gray-300">{uptimeMins}m</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">Engine</dt>
          <dd className="text-accent-glow">{health.inference_engine}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">Camera</dt>
          <dd className="text-gray-300">{health.camera_backend}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">Network</dt>
          <dd className="text-gray-300">{health.network_mode}</dd>
        </div>
      </dl>
    </div>
  );
}
