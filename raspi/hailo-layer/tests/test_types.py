"""Dataclass construction sanity."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from hailo_layer.types import BBox, Detection, FrameResult


def test_bbox_detection_frame_construction():
    bbox = BBox(0.1, 0.2, 0.3, 0.4)
    det = Detection("person", 0, 0.95, bbox)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = FrameResult(frame, (det,), 5.5)
    assert result.detections[0].label == "person"
    assert result.latency_ms == 5.5
    assert result.frame.shape == (480, 640, 3)


def test_dataclasses_are_frozen():
    det = Detection("person", 0, 0.9, BBox(0, 0, 1, 1))
    with pytest.raises(FrozenInstanceError):
        det.confidence = 0.5  # type: ignore[misc]
