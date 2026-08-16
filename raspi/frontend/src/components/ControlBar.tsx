interface ControlBarProps {
  connected: boolean;
  motorEnabled: boolean;
}

export function ControlBar({ connected, motorEnabled }: ControlBarProps) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-surface-raised border-b border-surface-overlay">
      <h1 className="text-sm font-mono font-semibold tracking-tight">
        Object Detection
      </h1>
      <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500">
        <span className={connected ? "text-success" : "text-danger"}>
          {connected ? "● STREAM" : "○ STREAM"}
        </span>
        <span className={motorEnabled ? "text-success" : "text-gray-600"}>
          {motorEnabled ? "● MOTOR" : "○ MOTOR"}
        </span>
      </div>
    </div>
  );
}
