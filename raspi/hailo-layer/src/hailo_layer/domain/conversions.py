"""Conversion between the hailo layer's dataclasses and the server's engine-contract dicts.

The dict shape mirrors the ONNX postprocess in
``raspi/server/app/services/inference_service.py`` exactly:
``{"class", "class_id", "confidence", "bbox": {"x", "y", "width", "height"}}``
in integer pixel coordinates — so the WebSocket payload is identical for both
engines and the frontend stays untouched.
"""

from __future__ import annotations

from typing import Any

from hailo_layer.types import BBox, Detection, FrameResult


def bbox_to_pixels(bbox: BBox, width: int, height: int) -> tuple[int, int, int, int]:
    """Convert a normalized [0,1] box to integer pixel (x, y, w, h), clamped to the frame."""
    x = max(0, min(width, int(round(bbox.xmin * width))))
    y = max(0, min(height, int(round(bbox.ymin * height))))
    w = max(0, min(width - x, int(round(bbox.width * width))))
    h = max(0, min(height - y, int(round(bbox.height * height))))
    return x, y, w, h


def detection_to_dict(d: Detection, width: int, height: int) -> dict[str, Any]:
    """One detection → server engine-contract dict."""
    x, y, w, h = bbox_to_pixels(d.bbox, width, height)
    return {
        "class": d.label,
        "class_id": d.class_id,
        "confidence": round(d.confidence, 4),
        "bbox": {"x": x, "y": y, "width": w, "height": h},
    }


def to_dicts(result: FrameResult) -> list[dict[str, Any]]:
    """All detections in a frame → list of engine-contract dicts."""
    h, w = result.frame.shape[:2]
    return [detection_to_dict(d, w, h) for d in result.detections]
