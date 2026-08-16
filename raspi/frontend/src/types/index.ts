/** A single detected object with bounding box. */
export interface Detection {
  class: string;
  class_id: number;
  confidence: number;
  bbox: BoundingBox;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** JSON message received over WebSocket alongside video frames. */
export interface DetectionFrame {
  type: "detections";
  timestamp: number;
  fps: number;
  inference_ms: number;
  objects: Detection[];
}

/** Motor status returned by the control API. */
export interface MotorStatus {
  uart_connected: boolean;
  mcu_responding: boolean;
  last_command: { left: number; right: number } | null;
}

/** System health snapshot. */
export interface SystemHealth {
  cpu_temp_c: number | null;
  npu_temp_c: number | null;
  uptime_seconds: number;
  fps: number;
  inference_engine: string;
  camera_backend: string;
  network_mode: string;
}

/** Joystick position (normalized -1 to 1). */
export interface JoystickPosition {
  x: number;
  y: number;
}
