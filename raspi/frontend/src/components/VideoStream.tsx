import type React from "react";

interface VideoStreamProps {
  videoRef: React.RefObject<HTMLImageElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  connected: boolean;
}

export function VideoStream({ videoRef, canvasRef, connected }: VideoStreamProps) {
  return (
    <div className="relative w-full max-w-[640px] aspect-[4/3] bg-black rounded-lg overflow-hidden border border-surface-overlay">
      {/* The video image — updated via blob URL */}
      <img
        ref={videoRef}
        alt="Camera stream"
        className="absolute inset-0 w-full h-full object-contain"
      />

      {/* Canvas overlay for bounding boxes */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />

      {/* Connection status overlay */}
      {!connected && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/70">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <span className="text-sm text-gray-400">Connecting to stream...</span>
          </div>
        </div>
      )}

      {/* No video yet */}
      {connected && (
        <div className="absolute top-2 left-2 px-2 py-1 rounded bg-surface/80 text-xs font-mono text-success">
          ● LIVE
        </div>
      )}
    </div>
  );
}
