import { VideoStream } from "./components/VideoStream";
import { DualJoystick } from "./components/DualJoystick";
import { DetectionPanel } from "./components/DetectionPanel";
import { SystemStatus } from "./components/SystemStatus";
import { ControlBar } from "./components/ControlBar";
import { useWebSocket } from "./hooks/useWebSocket";
import { useJoystick } from "./hooks/useJoystick";
import { useCallback } from "react";
import type { JoystickPosition } from "./types";

export default function App() {
  const {
    videoRef,
    canvasRef,
    connected,
    detections,
    fps,
    inferenceMs,
    systemHealth,
    fetchHealth,
  } = useWebSocket();

  const handleJoystickChange = useCallback(
    (_id: string, _pos: JoystickPosition) => {
      // Motor commands are sent directly in the hook
    },
    []
  );

  const handleJoystickRelease = useCallback(
    (_id: string) => {
      // Stop motors on release
      fetch("/api/control/stop", { method: "POST" }).catch(() => {});
    },
    []
  );

  const { leftRef, rightRef, leftState, rightState } = useJoystick({
    onChange: handleJoystickChange,
    onRelease: handleJoystickRelease,
  });

  const motorEnabled = systemHealth?.inference_engine !== undefined;

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <ControlBar connected={connected} motorEnabled={motorEnabled} />

      {/* Main content: responsive grid */}
      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-[1200px] mx-auto w-full">
        {/* Left: Video Feed */}
        <div className="flex-1 flex flex-col items-center gap-4">
          <VideoStream
            videoRef={videoRef}
            canvasRef={canvasRef}
            connected={connected}
          />

          {/* Joysticks (below video on mobile, visible on all sizes) */}
          <DualJoystick
            leftRef={leftRef}
            rightRef={rightRef}
            leftPos={leftState.position}
            rightPos={rightState.position}
            leftActive={leftState.active}
            rightActive={rightState.active}
          />
        </div>

        {/* Right: Panels */}
        <div className="flex flex-col gap-4 lg:w-64 flex-shrink-0">
          <SystemStatus health={systemHealth} onRefresh={fetchHealth} />
          <DetectionPanel
            detections={detections}
            fps={fps}
            inferenceMs={inferenceMs}
          />

          {/* Quick stop button */}
          <button
            onPointerDown={() =>
              fetch("/api/control/stop", { method: "POST" }).catch(() => {})
            }
            className="w-full py-3 rounded-lg bg-danger/20 border border-danger/50 text-danger text-sm font-mono font-semibold hover:bg-danger/30 active:bg-danger/40 transition-colors select-none"
          >
            ⏹ STOP MOTORS
          </button>
        </div>
      </div>
    </div>
  );
}
