"""FastAPI application entry point — object detection + motor control server."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_control import router as control_router
from app.api.routes_stream import router as stream_router
from app.api.routes_system import router as system_router
from app.config import settings
from app.services.camera_service import camera_service
from app.services.inference_service import inference_service
from app.services.motor_service import motor_service
from app.services.stream_service import stream_service

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init hardware services. Shutdown: clean release."""
    logger.info("══╡ Object Detection Server Starting ╞══")
    logger.info("Camera:  %s @ %s", settings.camera_backend, settings.camera_device)
    logger.info("Inference: %s", settings.inference_engine)
    logger.info("Motor: %s", "enabled" if settings.motor_enabled else "disabled")

    # Init hardware in dependency order
    camera_service.start()
    motor_service.initialize()

    # Init inference (may fail gracefully if no model)
    try:
        inference_service.initialize()
    except FileNotFoundError:
        logger.warning(
            "Model not found at %s — inference disabled. "
            "Place a YOLOv8 ONNX model or run scripts/compile_model.py",
            settings.model_path_resolved,
        )
    except Exception as e:
        logger.error("Inference init failed: %s", e)

    # Start streaming
    await stream_service.start()

    logger.info("══╡ Server Ready on port %d ╞══", settings.server_port)
    yield

    # Shutdown
    logger.info("══╡ Shutting down ╞══")
    await stream_service.stop()
    inference_service.shutdown()
    motor_service.shutdown()
    camera_service.stop()
    logger.info("══╡ Server stopped ╞══")


# ── App ──────────────────────────────────────────────────
app = FastAPI(
    title="Object Detection Server",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow any origin for LAN access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────
app.include_router(stream_router)
app.include_router(control_router)
app.include_router(system_router)


@app.get("/api/hello")
async def root():
    """Health check endpoint."""
    return {
        "service": "object-detection-server",
        "version": "0.1.0",
        "camera": camera_service.is_running,
        "inference": inference_service.is_initialized,
    }


# ── Static Frontend (production) ─────────────────────────
static_dir = settings.static_dir_resolved
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
    logger.info("Frontend static files: %s", static_dir)
else:
    logger.info("Frontend not built — run: cd ../frontend && npm run build")
