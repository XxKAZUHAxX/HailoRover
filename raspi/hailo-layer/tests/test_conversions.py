"""Engine-contract conversion: normalized boxes → clamped pixel dicts."""

import numpy as np

from hailo_layer.domain.conversions import bbox_to_pixels, detection_to_dict, to_dicts
from hailo_layer.types import BBox, Detection, FrameResult


def test_bbox_to_pixels_basic():
    # Box covering the left half of a 640x480 frame
    x, y, w, h = bbox_to_pixels(BBox(0.0, 0.0, 0.5, 1.0), 640, 480)
    assert (x, y, w, h) == (0, 0, 320, 480)


def test_bbox_to_pixels_rounds_and_clamps():
    # Normalized box slightly out of bounds → clamped to frame edges
    x, y, w, h = bbox_to_pixels(BBox(0.99, -0.01, 0.5, 1.5), 100, 100)
    assert x == 99
    assert y == 0
    assert w == 1       # clamped to width - x
    assert h == 100     # clamped to height - y


def test_detection_to_dict_contract_shape():
    d = Detection(label="person", class_id=0, confidence=0.91234, bbox=BBox(0.25, 0.25, 0.5, 0.5))
    out = detection_to_dict(d, 640, 480)
    assert out["class"] == "person"
    assert out["class_id"] == 0
    assert out["confidence"] == 0.9123  # rounded to 4 dp
    assert out["bbox"] == {"x": 160, "y": 120, "width": 320, "height": 240}


def test_to_dicts_uses_frame_dims():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det = Detection(label="car", class_id=2, confidence=0.8, bbox=BBox(0.5, 0.5, 0.25, 0.25))
    result = FrameResult(frame=frame, detections=(det,), latency_ms=3.2)
    out = to_dicts(result)
    assert len(out) == 1
    assert out[0]["bbox"] == {"x": 320, "y": 240, "width": 160, "height": 120}


def test_to_dicts_empty():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = FrameResult(frame=frame, detections=(), latency_ms=0.0)
    assert to_dicts(result) == []
