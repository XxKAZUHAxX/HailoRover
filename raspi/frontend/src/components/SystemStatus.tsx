import type { SystemHealth } from "../types";

interface SystemStatusProps {
  health: SystemHealth | null;
  onRefresh: () => void;
}

// °C thresholds: green → amber (warn) → red (danger + hot warning)
const CPU_WARN_C = 55;
const CPU_DANGER_C = 70;
const NPU_WARN_C = 65;
const NPU_DANGER_C = 80;

function tempColor(temp: number | null, warnC: number, dangerC: number): string {
  if (temp === null) return "text-gray-300";
  if (temp >= dangerC) return "text-danger";
  if (temp >= warnC) return "text-warning";
  return "text-success";
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

  const cpuTemp = health.cpu_temp_c;
  const npuTemp = health.npu_temp_c;

  // Danger-threshold warnings — shown when the chip is actually hot
  const hotWarnings: string[] = [];
  if (cpuTemp !== null && cpuTemp >= CPU_DANGER_C) {
    hotWarnings.push(`⚠ CPU hot (${cpuTemp.toFixed(1)}°C)`);
  }
  if (npuTemp !== null && npuTemp >= NPU_DANGER_C) {
    hotWarnings.push(`⚠ NPU hot (${npuTemp.toFixed(1)}°C)`);
  }

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
          <dd className={tempColor(cpuTemp, CPU_WARN_C, CPU_DANGER_C)}>
            {cpuTemp !== null ? `${cpuTemp.toFixed(1)}°C` : "—"}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">NPU Temp</dt>
          <dd className={tempColor(npuTemp, NPU_WARN_C, NPU_DANGER_C)}>
            {npuTemp !== null ? `${npuTemp.toFixed(1)}°C` : "—"}
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

      {hotWarnings.length > 0 && (
        <p className="mt-2 text-xs font-mono text-danger border border-danger/50 bg-danger/10 rounded px-2 py-1 animate-pulse">
          {hotWarnings.join("   ")}
        </p>
      )}
    </div>
  );
}
