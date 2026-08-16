"""Embedded-safe GStreamerDetectionApp.

Two fixes for running inside a server thread:

1. The parent ``__init__`` calls ``signal.signal(SIGINT, self.shutdown)``
   (gstreamer_app.py:264) — that raises ValueError off the main thread.
   Neutralized around ``super().__init__``.

2. The parent's default display sink is autovideosink, which needs a display.
   We force fakesink for headless operation.
"""

from __future__ import annotations

import signal

from hailo_layer.pipeline.hailo_compat import GStreamerDetectionApp


class ServerDetectionApp(GStreamerDetectionApp):
    """GStreamerDetectionApp that can be constructed off the main thread."""

    def __init__(self, app_callback, user_data, parser=None):
        orig_signal = signal.signal
        signal.signal = lambda *args, **kwargs: None  # no-op during parent construction
        try:
            super().__init__(app_callback, user_data, parser=parser)
        finally:
            signal.signal = orig_signal

    def get_pipeline_string(self) -> str:
        # Runs during create_pipeline() inside the parent __init__ — after the
        # parent set self.video_sink, so overriding it here is the reliable hook.
        self.video_sink = "fakesink"
        return super().get_pipeline_string()
