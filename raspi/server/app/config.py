"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Camera ──────────────────────────────────────────────
    camera_backend: str = "v4l2"          # "v4l2" (USB) or "libcamera" (MIPI CSI)
    camera_device: str = "/dev/video0"
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30

    # ── Inference ───────────────────────────────────────────
    inference_engine: str = "onnx"        # "onnx" (CPU) or "hailo" (NPU)
    model_path: str = "models/yolov8n.onnx"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    coco_names_path: str = "models/coco.names"

    # ── UART / Motor ────────────────────────────────────────
    uart_port: str = "/dev/ttyAMA0"
    uart_baud: int = 115200
    motor_enabled: bool = False           # Disabled until STM32 is connected

    # ── Network ─────────────────────────────────────────────
    network_mode: str = "lan"             # "lan" or "hotspot"
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # ── Frontend ────────────────────────────────────────────
    static_dir: str = "frontend-dist"     # Path to React build output

    # ── Stream ──────────────────────────────────────────────
    stream_quality: int = 80              # JPEG encode quality (1-100)

    @property
    def model_path_resolved(self) -> Path:
        """Absolute path to the model file."""
        path = Path(self.model_path)
        if not path.is_absolute():
            return Path(__file__).resolve().parent.parent / path
        return path

    @property
    def static_dir_resolved(self) -> Path:
        """Absolute path to the static frontend directory."""
        path = Path(self.static_dir)
        if not path.is_absolute():
            return Path(__file__).resolve().parent.parent / path
        return path


settings = Settings()
