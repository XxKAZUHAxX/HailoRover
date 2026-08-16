"""Hailo NPU interface — pipeline-takeover mode.

The GStreamer detection pipeline (``hailo_layer.pipeline.PipelineRunner``) owns
the camera and inference in a background thread and pushes
``FrameResult(BGR frame, detections, latency_ms)`` into a drop-oldest
FrameQueue. ``HailoRuntime`` is the server-side facade: start/stop the pipeline
thread and consume results.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from hailo_layer.config import PipelineOptions
from hailo_layer.types import FrameResult

logger = logging.getLogger(__name__)


class HailoRuntime:
    """Runs the hailo_layer GStreamer pipeline and exposes frame results."""

    def __init__(
        self,
        hef_path: str,
        labels_json: str | None = None,
        arch: str | None = None,
        input_source: str = "/dev/video0",
        width: int = 640,
        height: int = 480,
        frame_rate: int = 30,
        queue_size: int = 2,
        watchdog: bool = False,
        startup_timeout: float = 60.0,
    ) -> None:
        self._options = PipelineOptions(
            hef_path=hef_path,
            labels_json=labels_json,
            arch=arch,
            input_source=input_source,
            width=width,
            height=height,
            frame_rate=frame_rate,
            watchdog=watchdog,
            queue_size=queue_size,
            startup_timeout=startup_timeout,
        )
        self._queue = None
        self._runner = None

    def initialize(self) -> None:
        """Start the GStreamer pipeline thread and wait until it is ready."""
        # Lazy imports: hailo_layer.pipeline is Pi-only (gi/hailo/GStreamer).
        from hailo_layer.domain.frame_queue import FrameQueue
        from hailo_layer.pipeline.runner import PipelineRunner

        self._queue = FrameQueue(maxsize=self._options.queue_size)
        self._runner = PipelineRunner(self._options, self._queue)
        self._runner.start()
        self._runner.wait_ready(timeout=self._options.startup_timeout)  # raises on failure
        logger.info(
            "Hailo pipeline started: hef=%s arch=%s input=%s %dx%d",
            self._options.hef_path,
            self._options.arch or "auto",
            self._options.input_source,
            self._options.width,
            self._options.height,
        )

    def read(self) -> FrameResult | None:
        """Pop the newest (frame, detections, latency) — None when empty or stopped."""
        if self._runner is None or not self._runner.is_alive:
            return None
        return self._queue.pop_nowait() if self._queue is not None else None

    def infer(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Legacy sync contract — unused in pipeline mode (detections arrive with frames)."""
        return []

    def shutdown(self) -> None:
        """Stop the pipeline thread and join it."""
        if self._runner is not None:
            self._runner.stop()
            self._runner = None
        self._queue = None
