"""REST endpoints for system health, config, and monitoring."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import ConfigUpdate, SystemHealth
from app.services.camera_service import camera_service
from app.services.inference_service import inference_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])

# Track server start time
_START_TIME = time.time()


def _read_cpu_temp() -> float | None:
    """Read Raspberry Pi CPU temperature from sysfs."""
    temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if temp_path.exists():
        try:
            return float(temp_path.read_text().strip()) / 1000.0
        except (ValueError, OSError):
            pass
    return None


@router.get("/health", response_model=SystemHealth)
async def health() -> SystemHealth:
    """System health snapshot: temps, uptime, FPS, engine status."""
    return SystemHealth(
        cpu_temp_c=_read_cpu_temp(),
        npu_temp_c=None,  # TODO: Hailo temperature via HailoRT
        uptime_seconds=round(time.time() - _START_TIME, 1),
        fps=round(camera_service.fps, 1),
        inference_engine=settings.inference_engine,
        camera_backend=settings.camera_backend,
        network_mode=settings.network_mode,
    )


@router.get("/config")
async def get_config() -> dict:
    """Return the current runtime configuration (safe subset)."""
    return {
        "camera_backend": settings.camera_backend,
        "camera_width": settings.camera_width,
        "camera_height": settings.camera_height,
        "camera_fps": settings.camera_fps,
        "inference_engine": settings.inference_engine,
        "confidence_threshold": settings.confidence_threshold,
        "network_mode": settings.network_mode,
        "motor_enabled": settings.motor_enabled,
        "server_port": settings.server_port,
    }


@router.patch("/config")
async def update_config(update: ConfigUpdate) -> dict:
    """Dynamically update select config values at runtime."""
    if update.confidence_threshold is not None:
        settings.confidence_threshold = update.confidence_threshold
        logger.info("Confidence threshold → %.2f", update.confidence_threshold)
    if update.network_mode is not None:
        settings.network_mode = update.network_mode
        logger.info("Network mode → %s", update.network_mode)
    if update.motor_enabled is not None:
        settings.motor_enabled = update.motor_enabled
        logger.info("Motor enabled → %s", update.motor_enabled)
    return await get_config()
