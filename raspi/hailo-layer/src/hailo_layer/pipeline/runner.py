"""PipelineRunner — owns the GStreamer pipeline thread lifecycle.

Everything hailo/GStreamer-related is constructed and run in one dedicated
daemon thread: the pipeline + GLib MainLoop must live in the same thread, and
``app.run()`` ends with ``sys.exit`` which would kill the server on the main
thread — here it raises SystemExit locally and is caught.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from hailo_layer.config import PipelineOptions
from hailo_layer.domain.frame_queue import FrameQueue
from hailo_layer.pipeline.hailo_compat import check_hailo_apps_version

logger = logging.getLogger(__name__)


def _snapshot_root_logging() -> tuple[int, list[Any]]:
    root = logging.getLogger()
    return root.level, list(root.handlers)


def _restore_root_logging(snapshot: tuple[int, list[Any]]) -> None:
    # hailo-apps init_logging(force=True) removes all root handlers; restore ours.
    root = logging.getLogger()
    root.handlers[:] = snapshot[1]
    root.setLevel(snapshot[0])


class PipelineRunner:
    """Starts/stops the embedded GStreamerDetectionApp on a dedicated thread."""

    def __init__(self, options: PipelineOptions, queue: FrameQueue) -> None:
        self._options = options
        self._queue = queue
        self._thread: threading.Thread | None = None
        self._app: Any = None
        self._ready = threading.Event()
        self._exit_code: int | None = None
        self._error: BaseException | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("PipelineRunner already started")
        check_hailo_apps_version()  # fail fast, with upgrade hint (hailo_compat)
        self._thread = threading.Thread(
            target=self._thread_main, name="hailo-pipeline", daemon=True
        )
        self._thread.start()

    def _thread_main(self) -> None:
        from hailo_layer.pipeline.callback import make_user_callback
        from hailo_layer.pipeline.hailo_compat import app_callback_class
        from hailo_layer.pipeline.server_app import ServerDetectionApp
        from hailo_layer.pipeline.server_parser import build_server_parser

        snapshot = _snapshot_root_logging()
        try:
            parser = build_server_parser(self._options)
            user_data = app_callback_class()
            latency_holder = [time.monotonic()]
            callback = make_user_callback(self._queue, latency_holder)
            self._app = ServerDetectionApp(callback, user_data, parser=parser)
            _restore_root_logging(snapshot)
            self._ready.set()  # construction + pipeline parse succeeded
            self._app.run()    # blocks; ends with sys.exit(0|1)
        except SystemExit as e:
            self._exit_code = int(e.code or 0)
        except BaseException as e:
            self._error = e
            self._exit_code = 1
            logger.exception("Hailo pipeline thread failed")
        finally:
            _restore_root_logging(snapshot)
            self._ready.set()  # unblock any waiter

    def wait_ready(self, timeout: float | None = None) -> None:
        """Block until the pipeline is constructed (or failed)."""
        timeout = timeout if timeout is not None else self._options.startup_timeout
        self._ready.wait(timeout=timeout)
        if not self._ready.is_set():
            raise RuntimeError(
                f"Hailo pipeline failed to start within {timeout:.0f}s "
                "(first run may download the HEF)"
            )
        if self._exit_code:
            raise RuntimeError(
                f"Hailo pipeline exited during startup (code {self._exit_code}); "
                f"last error: {self._error}"
            )

    def stop(self, timeout: float = 15.0) -> None:
        """Stop the pipeline and join the thread."""
        thread = self._thread
        if thread is None:
            return
        for attempt in range(3):  # handles stop-during-construction race
            app = self._app
            if app is not None:
                try:
                    app.shutdown()
                except Exception:
                    pass
            thread.join(timeout=(timeout if attempt == 0 else 5.0))
            if not thread.is_alive():
                break
        else:
            loop = getattr(self._app, "loop", None)
            if loop is not None:
                try:
                    loop.quit()  # g_main_loop_quit — thread-safe forced stop
                except Exception:
                    pass
            thread.join(timeout=5.0)
        self._queue.clear()
        self._thread = None
        self._app = None

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
