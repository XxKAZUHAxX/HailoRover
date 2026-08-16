"""Pure-Python domain layer: queues and conversions, no hailo imports."""

from hailo_layer.domain.conversions import detection_to_dict, to_dicts
from hailo_layer.domain.frame_queue import FrameQueue

__all__ = ["FrameQueue", "detection_to_dict", "to_dicts"]
