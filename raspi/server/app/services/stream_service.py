"""Stream service — encodes frames to JPEG and manages WebSocket broadcast."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import cv2
import numpy as np

from app.config import settings
from app.services.camera_service import camera_service
from app.services.inference_service import inference_service

logger = logging.getLogger(__name__)


class StreamService:
    """Captures frames, runs inference, and encodes MJPEG for broadcasting."""

    def __init__(self) -> None:
        # Each WebSocket client gets an entry: { "queue": asyncio.Queue, "last_frame": int }
        self._clients: dict[int, dict[str, Any]] = {}
        self._client_id_counter = 0
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._fps = 0.0

    async def start(self) -> None:
        """Start the frame capture + broadcast loop."""
        self._running = True
        self._task = asyncio.create_task(self._broadcast_loop())
        logger.info("Stream service started")

    async def stop(self) -> None:
        """Stop the broadcast loop and disconnect all clients."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Close all client queues
        for entry in self._clients.values():
            await entry["queue"].put(None)  # Sentinel to signal end
        self._clients.clear()
        logger.info("Stream service stopped")

    def register_client(self) -> tuple[int, asyncio.Queue[bytes | str | None]]:
        """Register a new WebSocket client. Returns (client_id, queue)."""
        client_id = self._client_id_counter
        self._client_id_counter += 1
        queue: asyncio.Queue[bytes | str | None] = asyncio.Queue(maxsize=10)
        self._clients[client_id] = {"queue": queue, "last_frame": -1}
        logger.debug("Client %d registered (%d total)", client_id, len(self._clients))
        return client_id, queue

    def unregister_client(self, client_id: int) -> None:
        """Remove a disconnected client."""
        self._clients.pop(client_id, None)
        logger.debug("Client %d unregistered (%d remaining)", client_id, len(self._clients))

    async def _broadcast_loop(self) -> None:
        """Main loop: read frame → infer → encode → push to all client queues."""
        frame_count = 0
        fps_start = time.monotonic()

        while self._running:
            frame = camera_service.read()
            if frame is None:
                await asyncio.sleep(0.001)  # 1ms yield
                continue

            # Run inference (synchronously — ONNX releases GIL, Hailo is non-blocking)
            detections = inference_service.detect(frame) if inference_service.is_initialized else []

            # Encode JPEG
            encode_success, jpeg_bytes = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, settings.stream_quality]
            )
            if not encode_success:
                logger.error("JPEG encode failed for frame — dropping")
                continue
            jpeg_data = jpeg_bytes.tobytes()

            # Frame-flow diagnostics: log first frame and then every 50
            frame_count += 1
            if frame_count == 1 or frame_count % 50 == 0:
                logger.info(
                    "Stream: frame %d (%d KB) sent to %d client(s) — %.1f fps",
                    frame_count, len(jpeg_data) // 1024,
                    len(self._clients), self._fps,
                )

            # Build detection JSON
            detection_msg = json.dumps({
                "type": "detections",
                "timestamp": time.time(),
                "fps": round(camera_service.fps, 1),
                "inference_ms": round(inference_service.inference_time_ms, 1),
                "objects": detections,
            })

            # Push to all connected clients
            stale_clients = []
            for cid, entry in self._clients.items():
                queue: asyncio.Queue = entry["queue"]
                if queue.full():
                    # Client is too slow — drain and replace oldest
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                try:
                    queue.put_nowait(jpeg_data)       # binary frame
                    queue.put_nowait(detection_msg)   # JSON text
                except asyncio.QueueFull:
                    stale_clients.append(cid)

            for cid in stale_clients:
                self.unregister_client(cid)

            # FPS calculation
            frame_count += 1
            elapsed = time.monotonic() - fps_start
            if elapsed >= 1.0:
                self._fps = frame_count / elapsed
                frame_count = 0
                fps_start = time.monotonic()

    @property
    def fps(self) -> float:
        return self._fps


# Module-level singleton
stream_service = StreamService()
