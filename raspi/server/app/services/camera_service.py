"""Camera lifecycle management — wraps the HAL with error recovery."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Optional

import numpy as np

from app.config import settings
from app.hal.camera_hal import CameraBackend, create_camera

logger = logging.getLogger(__name__)


class CameraService:
    """Manages the camera lifecycle: open, read, reconnect on failure."""

    def __init__(self) -> None:
        self._camera: CameraBackend | None = None
        self._lock = threading.Lock()
        self._fps_buffer: deque[float] = deque(maxlen=30)
        self._last_frame_time = time.monotonic()
        self._current_fps = 0.0
        self._consecutive_failures = 0
        # Threshold: ~0.5s of continuous read failures triggers a reopen
        self._failure_threshold = 10

    def start(self) -> None:
        """Open the camera and begin capture."""
        with self._lock:
            self._camera = create_camera()
            self._camera.open()
            logger.info(
                "Camera started: %s @ %dx%d",
                settings.camera_backend,
                settings.camera_width,
                settings.camera_height,
            )

    def read(self) -> np.ndarray | None:
        """Read the next frame. Returns None if the camera is not available.

        Watchdog: after N consecutive failed reads (e.g. V4L2 buffer corruption
        from a second process opening the device, USB hiccup, etc.), the camera
        is closed and reopened transparently.
        """
        with self._lock:
            if self._camera is None or not self._camera.is_open:
                return None
            frame = self._camera.read()

            if frame is None:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._failure_threshold:
                    logger.warning(
                        "Camera read failed %d times consecutively — reopening device",
                        self._consecutive_failures,
                    )
                    self._reopen_unlocked()
            else:
                self._consecutive_failures = 0

        if frame is not None:
            now = time.monotonic()
            elapsed = now - self._last_frame_time
            self._last_frame_time = now
            if elapsed > 0:
                self._fps_buffer.append(1.0 / elapsed)
                self._current_fps = sum(self._fps_buffer) / len(self._fps_buffer)

        return frame

    def _reopen_unlocked(self) -> None:
        """Close and reopen the camera. Caller must hold self._lock."""
        if self._camera is not None:
            try:
                self._camera.close()
            except Exception as e:
                logger.debug("Error closing broken camera: %s", e)
            self._camera = None
        try:
            self._camera = create_camera()
            self._camera.open()
            logger.info("Camera reopened after failure")
        except Exception as e:
            logger.error("Camera reopen failed: %s — will retry on next reads", e)
            self._camera = None
        self._consecutive_failures = 0

    @property
    def fps(self) -> float:
        """Current measured FPS (30-frame rolling average)."""
        return self._current_fps

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._camera is not None and self._camera.is_open

    def stop(self) -> None:
        """Close the camera."""
        with self._lock:
            if self._camera is not None:
                self._camera.close()
                self._camera = None
            logger.info("Camera stopped")


# Module-level singleton — initialized in app lifespan
camera_service = CameraService()
