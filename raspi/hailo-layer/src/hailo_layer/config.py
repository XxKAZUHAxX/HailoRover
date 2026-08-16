"""Pipeline configuration for the embedded GStreamer detection app.

Pure Python — no hailo imports. Values flow in from the server's settings
(``hailo_hal.HailoRuntime``) or from environment variables (``from_env``,
used by the ``hailo-smoke`` CLI).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class PipelineOptions:
    """All knobs for the embedded GStreamerDetectionApp."""

    hef_path: str | None = None          # HEF name ("yolov8m") or path; None → per-arch default
    labels_json: str | None = None       # Labels JSON for hailofilter; None → model default (COCO-80)
    arch: str | None = None              # "hailo8" | "hailo8l" | "hailo10h"; None → auto-detect
    input_source: str = "/dev/video0"    # v4l2 device path, "usb" (auto), or "rpi" (CSI)
    width: int = 640
    height: int = 480
    frame_rate: int = 30                 # informational; the USB/MJPEG pipeline path hardcodes 30
    batch_size: int = 2
    watchdog: bool = False               # hailo-apps pipeline watchdog (rebuild on stall)
    queue_size: int = 2                  # FrameQueue depth (drop-oldest)
    startup_timeout: float = 60.0        # s; first run may auto-download the HEF

    @classmethod
    def from_env(cls) -> "PipelineOptions":
        """Build options from HAILO_* environment variables."""
        return cls(
            hef_path=os.environ.get("HEF_PATH") or None,
            labels_json=os.environ.get("LABELS_JSON") or None,
            arch=os.environ.get("HAILO_ARCH") or None,
            input_source=os.environ.get("HAILO_INPUT", "/dev/video0"),
            width=_env_int("HAILO_WIDTH", 640),
            height=_env_int("HAILO_HEIGHT", 480),
            frame_rate=_env_int("HAILO_FRAME_RATE", 30),
            batch_size=_env_int("HAILO_BATCH_SIZE", 2),
            watchdog=_env_bool("HAILO_WATCHDOG", False),
            queue_size=_env_int("HAILO_QUEUE_SIZE", 2),
            startup_timeout=_env_float("HAILO_STARTUP_TIMEOUT", 60.0),
        )
