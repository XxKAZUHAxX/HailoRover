"""argv-injecting argparse parser for embedding GStreamerDetectionApp in a server.

``GStreamerApp.__init__`` calls ``args.parse_args()`` with no arguments
(gstreamer_app.py:253), which reads ``sys.argv[1:]`` — inside the server that's
uvicorn's argv and would crash the app. ServerArgParser overrides both
``parse_args`` and ``parse_known_args`` to parse a fixed (empty) argv list into
a namespace pre-seeded with our overrides.
"""

from __future__ import annotations

import argparse
from typing import Any

from hailo_layer.config import PipelineOptions


class ServerArgParser(argparse.ArgumentParser):
    """An ArgumentParser whose parse methods never touch sys.argv."""

    def __init__(
        self,
        argv: list[str] | None = None,
        overrides: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._argv = list(argv) if argv is not None else []
        self._overrides = dict(overrides or {})

    def parse_args(self, args=None, namespace=None):
        ns = argparse.Namespace(**self._overrides)
        return super().parse_args(self._argv, namespace=ns)

    def parse_known_args(self, args=None, namespace=None):
        ns = argparse.Namespace(**self._overrides)
        return super().parse_known_args(self._argv, namespace=ns)


def build_server_parser(options: PipelineOptions) -> ServerArgParser:
    """Build a parser with hailo-apps' full option set, fixed argv, and our overrides.

    Namespace pre-sets win over parser defaults; the injected argv is empty so
    nothing external (uvicorn args) can override them.
    """
    from hailo_layer.pipeline.hailo_compat import get_pipeline_parser

    return ServerArgParser(
        argv=[],
        overrides={
            "input": options.input_source,
            "width": options.width,
            "height": options.height,
            "frame_rate": options.frame_rate,
            "hef_path": options.hef_path,
            "labels_json": options.labels_json,
            "arch": options.arch,
            "batch_size": options.batch_size,
            "enable_watchdog": options.watchdog,
            "use_frame": False,          # we extract frames ourselves in the callback
            "show_fps": False,
            "disable_callback": False,
            "disable_sync": False,
            "dump_dot": False,
            "print_pipeline": False,
            "horizontal_mirror": False,
            "vertical_mirror": False,
        },
        parents=[get_pipeline_parser()],
        add_help=False,
    )
