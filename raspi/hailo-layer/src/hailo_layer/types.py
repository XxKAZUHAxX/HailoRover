"""Core dataclasses shared across the hailo layer.

Pure Python — no hailo/GStreamer imports, so this module (and the domain
package) is unit-testable on any machine.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BBox:
    """Axis-aligned box in normalized [0,1] coordinates (Hailo native)."""

    xmin: float
    ymin: float
    width: float
    height: float


@dataclass(frozen=True)
class Detection:
    """One object detection.

    ``label`` comes from the HEF's labels (or the TAPPAS postprocess .so's
    built-in COCO-80 defaults); ``bbox`` is normalized.
    """

    label: str
    class_id: int
    confidence: float
    bbox: BBox


@dataclass(frozen=True)
class FrameResult:
    """One pipeline result: a frame plus its detections, server-format ready.

    ``frame`` is BGR uint8 HxWx3 (what cv2.imencode expects).
    """

    frame: np.ndarray
    detections: tuple[Detection, ...]
    latency_ms: float
