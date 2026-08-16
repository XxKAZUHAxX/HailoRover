"""hailo-layer — Hailo GStreamer inference layer for the HailoRover server.

Layering:
- ``hailo_layer.types`` / ``hailo_layer.domain`` — pure Python, no hailo or
  GStreamer imports; unit-testable on any machine.
- ``hailo_layer.pipeline`` — hailo/GStreamer-aware; import only on the Pi
  (inside ``venv_hailo_apps``).

Version pairing (see raspi/docs/hailo-setup.md):
    hailo-layer 0.1.x  ↔  hailo-apps 26.03.x  ↔  HailoRT 4.23  ↔  TAPPAS 5.1
"""

from hailo_layer.domain.conversions import detection_to_dict, to_dicts
from hailo_layer.domain.frame_queue import FrameQueue
from hailo_layer.types import BBox, Detection, FrameResult

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BBox",
    "Detection",
    "FrameResult",
    "FrameQueue",
    "detection_to_dict",
    "to_dicts",
]
