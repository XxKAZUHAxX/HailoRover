"""REST endpoints for system health, config, and monitoring."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import ConfigUpdate, SystemHealth
from app.services.camera_service import camera_service
from app.services.inference_service import inference_service
from app.services.stream_service import stream_service

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


_NPU_TEMP_TTL_S = 15.0  # health is polled every ~5s; rate-limit chip control requests
_npu_temp_cache: dict[str, Any] = {"value": None, "at": 0.0}
_hailo_device: Any = None  # lazily-opened hailo_platform.Device control handle


def _get_hailo_device() -> Any:
    """Open (once) the Hailo device control handle via the legacy binding."""
    global _hailo_device
    if _hailo_device is None:
        from hailo_platform import Device  # Pi-only; ships with the hailoRT wheel

        _hailo_device = Device()
    return _hailo_device


def _read_npu_temp_sync() -> float | None:
    """Average of the chip's two internal temperature sensors (TS0/TS1).

    ``Device.control.get_chip_temperature()`` is the legacy ``hailo_platform``
    binding over the HailoRT control protocol — the newer ``hailo`` module
    does NOT expose it. Works while the pipeline runs (control channel shared).
    """
    if settings.inference_engine != "hailo":
        return None
    try:
        info = _get_hailo_device().control.get_chip_temperature()
    except Exception as e:
        logger.warning("NPU temp read failed: %s", e)
        return None
    return round((info.ts0_temperature + info.ts1_temperature) / 2.0, 2)


async def _read_npu_temp() -> float | None:
    """Cached NPU temperature (°C) — None when unavailable."""
    now = time.monotonic()
    if now - float(_npu_temp_cache["at"]) < _NPU_TEMP_TTL_S:
        return _npu_temp_cache["value"]
    value = await asyncio.to_thread(_read_npu_temp_sync)
    _npu_temp_cache["value"] = value
    _npu_temp_cache["at"] = now
    return value


@router.get("/health", response_model=SystemHealth)
async def health() -> SystemHealth:
    """System health snapshot: temps, uptime, FPS, engine status."""
    return SystemHealth(
        cpu_temp_c=_read_cpu_temp(),
        npu_temp_c=await _read_npu_temp(),
        uptime_seconds=round(time.time() - _START_TIME, 1),
        fps=round(
            stream_service.fps if settings.inference_engine == "hailo" else camera_service.fps, 1
        ),
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
