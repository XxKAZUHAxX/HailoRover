"""Handoff callback for the identity element (GStreamer streaming thread).

Must stay non-blocking: everything here is copies/conversions plus one
``put_nowait`` on the FrameQueue. No I/O, no locks, no GStreamer blocking calls.

Frame counting is handled automatically by the hailo-apps framework wrapper —
do NOT call ``increment()`` yourself.
"""

from __future__ import annotations

import logging
import os
import time

os.environ["GST_PLUGIN_FEATURE_RANK"] = "vaapidecodebin:NONE"  # hailo-apps boilerplate

import cv2  # noqa: E402
import hailo  # noqa: E402

from hailo_layer.domain.frame_queue import FrameQueue  # noqa: E402
from hailo_layer.pipeline.hailo_compat import (  # noqa: E402
    get_caps_from_pad,
    get_numpy_from_buffer,
)
from hailo_layer.types import BBox, Detection, FrameResult  # noqa: E402

logger = logging.getLogger(__name__)

_MAX_PLAUSIBLE_LATENCY_MS = 5000.0


def _latency_ms(buffer, holder: list[float]) -> float:
    """End-to-end latency estimate: buffer PTS (pipeline clock) vs wall clock.

    For a live v4l2 source the pipeline clock runs near-monotonic, so
    ``now - pts`` gives capture→callback latency. Falls back to callback cadence.
    """
    now = time.monotonic()
    pts = buffer.pts
    if pts is not None and pts >= 0:
        latency = (now - pts / 1e9) * 1000.0
        if 0.0 <= latency < _MAX_PLAUSIBLE_LATENCY_MS:
            return latency
    delta = (now - holder[0]) * 1000.0
    holder[0] = now
    return delta if 0.0 < delta < _MAX_PLAUSIBLE_LATENCY_MS else 0.0


def make_user_callback(
    queue: FrameQueue,
    latency_holder: list[float] | None = None,
):
    """Return a handoff callback ``(element, buffer, user_data)`` that pushes
    ``FrameResult(BGR frame, detections, latency_ms)`` into ``queue``."""

    holder = latency_holder if latency_holder is not None else [time.monotonic()]

    def app_callback(element, buffer, user_data):
        if buffer is None or not user_data.running:
            return
        pad = element.get_static_pad("src")
        if pad is None:
            return
        fmt, width, height = get_caps_from_pad(pad)
        if fmt is None or width is None or height is None:
            return
        try:
            frame_rgb = get_numpy_from_buffer(buffer, fmt, width, height)  # HxWx3 uint8 copy, RGB
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        except Exception:
            logger.exception("Callback frame extraction failed — dropping frame")
            return

        roi = hailo.get_roi_from_buffer(buffer)
        detections = []
        for det in roi.get_objects_typed(hailo.HAILO_DETECTION):
            bbox = det.get_bbox()
            detections.append(
                Detection(
                    label=det.get_label(),
                    class_id=int(det.get_class_id()),
                    confidence=float(det.get_confidence()),
                    bbox=BBox(
                        xmin=float(bbox.xmin()),
                        ymin=float(bbox.ymin()),
                        width=float(bbox.width()),
                        height=float(bbox.height()),
                    ),
                )
            )
        queue.push(
            FrameResult(
                frame=frame_bgr,
                detections=tuple(detections),
                latency_ms=_latency_ms(buffer, holder),
            )
        )

    return app_callback
