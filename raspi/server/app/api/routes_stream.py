"""WebSocket endpoint for MJPEG video stream + detection data."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stream_service import stream_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/stream")
async def video_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint that pushes MJPEG frames + detection JSON.

    Binary frames = JPEG images
    Text frames = JSON detection arrays
    """
    await websocket.accept()
    client_id, queue = stream_service.register_client()

    try:
        while True:
            message = await queue.get()
            if message is None:
                break  # Server shutdown
            if isinstance(message, bytes):
                await websocket.send_bytes(message)
            else:
                await websocket.send_text(message)
    except WebSocketDisconnect:
        logger.debug("WebSocket client %d disconnected", client_id)
    except asyncio.CancelledError:
        pass
    finally:
        stream_service.unregister_client(client_id)
        try:
            await websocket.close()
        except Exception:
            pass
