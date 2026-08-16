/**
 * Canvas-based bounding box renderer.
 * Draws detection boxes + labels on a <canvas> overlay positioned above the video.
 */

import type { Detection } from "../types";

const COLORS: Record<string, string> = {
  person: "#ef4444",
  car: "#f59e0b",
  truck: "#f97316",
  bus: "#f59e0b",
  motorcycle: "#84cc16",
  bicycle: "#22c55e",
  traffic_light: "#f59e0b",
  stop_sign: "#ef4444",
  dog: "#a855f7",
  cat: "#c084fc",
  default: "#3b82f6",
};

const FONT = "12px 'JetBrains Mono', monospace";

function getColor(_classId: number, className: string): string {
  return COLORS[className] ?? COLORS.default;
}

/**
 * Draw detection boxes on the canvas context.
 * Call this on every detection frame from the WebSocket.
 */
export function renderDetections(
  ctx: CanvasRenderingContext2D,
  detections: Detection[],
  canvasWidth: number,
  canvasHeight: number
): void {
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  for (const det of detections) {
    const { x, y, width, height } = det.bbox;
    const color = getColor(det.class_id, det.class);

    // Box
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);

    // Label background
    const label = `${det.class} ${(det.confidence * 100).toFixed(0)}%`;
    ctx.font = FONT;
    const metrics = ctx.measureText(label);
    const labelHeight = 18;
    const labelWidth = metrics.width + 8;

    ctx.fillStyle = color;
    ctx.fillRect(x, Math.max(y - labelHeight, 0), labelWidth, labelHeight);

    // Label text
    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, x + 4, Math.max(y - labelHeight, 0) + 13);
  }
}
