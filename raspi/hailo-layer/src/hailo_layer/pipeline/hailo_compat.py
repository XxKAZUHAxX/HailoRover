"""Single choke-point for hailo-apps / HailoRT imports and version policy.

The ``hailo-apps/`` checkout inside this repo is REFERENCE ONLY (gitignored).
All imports here resolve through the hailo-apps package pip-installed (editable)
into ``venv_hailo_apps`` on the Pi. **No other module in this project imports
``hailo_apps.*`` directly** — if a hailo-apps upgrade breaks something, the fix
lands here and only here.

UPGRADE PROCEDURE (hailo-apps publishes a new release):
  1. On the Pi: ``cd ~/hailo-apps && git fetch --tags && git checkout <new-tag> && pip install -e .``
  2. Edit the two constants below (and the pairing matrix in raspi/docs/hailo-setup.md).
  3. Run: ``hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30``
     and then the server WS check.
"""

from __future__ import annotations

import importlib.metadata

HAILO_APPS_MIN_VERSION = "26.03.0"   # inclusive
HAILO_APPS_MAX_VERSION = "26.04.0"   # exclusive — 26.03.x patch releases accepted automatically


def check_hailo_apps_version() -> None:
    """Raise RuntimeError (with upgrade hint) if hailo-apps is missing or out of range."""
    try:
        version = importlib.metadata.version("hailo-apps")
    except importlib.metadata.PackageNotFoundError as e:
        raise RuntimeError(
            "hailo-apps is not installed in this environment. "
            "See raspi/docs/hailo-setup.md: install hailo-apps into venv_hailo_apps."
        ) from e
    if not (HAILO_APPS_MIN_VERSION <= version < HAILO_APPS_MAX_VERSION):
        raise RuntimeError(
            f"hailo-apps {version} is outside the supported range "
            f"[{HAILO_APPS_MIN_VERSION}, {HAILO_APPS_MAX_VERSION}). Update the constants "
            f"in hailo_layer/pipeline/hailo_compat.py and rerun hailo-smoke."
        )


# ── Stable entry points used by this project ─────────────────────────────────
# These are the integration points hailo-apps' own examples use. Importing this
# module requires gi/hailo (Pi-only); the try/except keeps it importable anywhere.
try:
    from hailo_apps.python.core.common.buffer_utils import (  # noqa: F401
        get_caps_from_pad,
        get_numpy_from_buffer,
    )
    from hailo_apps.python.core.common.parser import get_pipeline_parser  # noqa: F401
    from hailo_apps.python.core.gstreamer.gstreamer_app import app_callback_class  # noqa: F401
    from hailo_apps.python.pipeline_apps.detection.detection_pipeline import (  # noqa: F401
        GStreamerDetectionApp,
    )

    _HAILO_APPS_AVAILABLE = True
except ImportError:  # importable on any platform; only the Pi imports this module
    _HAILO_APPS_AVAILABLE = False
