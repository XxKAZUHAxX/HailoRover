"""Camera hardware abstraction — supports USB (V4L2) and MIPI CSI (libcamera)."""

from __future__ import annotations

import time
from typing import Protocol

import cv2
import numpy as np

from app.config import settings


class CameraBackend(Protocol):
    """Interface for camera backends."""

    def open(self) -> None: ...
    def read(self) -> np.ndarray | None: ...
    def close(self) -> None: ...
    @property
    def is_open(self) -> bool: ...


class V4L2Camera:
    """USB / V4L2 camera backend via OpenCV."""

    def __init__(self, device: str = settings.camera_device) -> None:
        self.device = device
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self.device)
        # IMPORTANT: FOURCC must be set BEFORE resolution/FPS.
        # V4L2 picks the video mode based on fourcc + resolution together;
        # setting resolution first locks a mode and the fourcc change fails silently.
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)
        self._cap.set(cv2.CAP_PROP_FPS, settings.camera_fps)
        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open camera: {self.device}")
        # Log the actual negotiated settings
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
        fourcc = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        fourcc_str = "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4))
        import logging
        logging.getLogger(__name__).info(
            "Camera negotiated: %dx%d @ %.0f FPS, codec=%s",
            actual_w, actual_h, actual_fps, fourcc_str,
        )

    def read(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()


class LibcameraBackend:
    """MIPI CSI camera backend via picamera2 (Raspberry Pi native)."""

    def __init__(self) -> None:
        self._picam2 = None

    def open(self) -> None:
        try:
            from picamera2 import Picamera2  # type: ignore[import-untyped]
        except ImportError:
            raise RuntimeError(
                "picamera2 not installed. Install with: "
                "sudo apt install python3-picamera2"
            )
        self._picam2 = Picamera2()
        config = self._picam2.create_video_configuration(
            main={"size": (settings.camera_width, settings.camera_height)},
            controls={"FrameRate": settings.camera_fps},
        )
        self._picam2.configure(config)
        self._picam2.start()
        # Allow sensor to settle
        time.sleep(0.5)

    def read(self) -> np.ndarray | None:
        if self._picam2 is None:
            return None
        return self._picam2.capture_array()

    def close(self) -> None:
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2 = None

    @property
    def is_open(self) -> bool:
        return self._picam2 is not None


def create_camera() -> CameraBackend:
    """Factory: returns the camera backend for the configured mode."""
    if settings.camera_backend == "libcamera":
        return LibcameraBackend()
    return V4L2Camera()
