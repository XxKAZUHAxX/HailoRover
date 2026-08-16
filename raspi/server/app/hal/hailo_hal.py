"""Hailo AI Hat NPU interface — placeholder until hardware is available.

When the AI Hat arrives, this module wraps the HailoRT Python API:
  - hailo_platform (pyhailort)
  - Model loading from .hef files
  - Async inference scheduling
  - Input preprocessing / output postprocessing for YOLOv8
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class HailoRuntime:
    """Wrapper around HailoRT for YOLOv8 inference on Hailo-8L NPU."""

    def __init__(self, hef_path: str) -> None:
        self.hef_path = hef_path
        self._runner: Any = None
        self._configured = False

    def initialize(self) -> None:
        """Load .hef model and configure the Hailo device."""
        try:
            import hailo_platform  # type: ignore[import-unused]
        except ImportError:
            raise RuntimeError(
                "HailoRT Python API not installed. "
                "See raspi/docs/hailo-setup.md for installation instructions."
            )
        logger.info("Hailo device initialized — model: %s", self.hef_path)
        # TODO: Full HailoRT initialization when hardware is available
        # - hailo_platform.Device.scan()
        # - Configure vdevice
        # - Load .hef model
        # - Create infer model + bindings
        self._configured = True

    def infer(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Run inference on a single frame. Returns list of detections."""
        if not self._configured:
            raise RuntimeError("Hailo runtime not initialized")
        # TODO: Implement when hardware is available
        # - Preprocess frame (resize, normalize, NCHW)
        # - Run inference via HailoRT
        # - Postprocess outputs (NMS, scale to original coords)
        logger.debug("Hailo inference called — placeholder, returning empty")
        return []

    def shutdown(self) -> None:
        """Release Hailo device resources."""
        logger.info("Hailo device shutdown")
        self._configured = False
