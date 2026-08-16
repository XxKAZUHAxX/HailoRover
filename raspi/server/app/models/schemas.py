"""Pydantic models for API requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Detection ───────────────────────────────────────────

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class Detection(BaseModel):
    class_name: str = Field(alias="class")
    class_id: int
    confidence: float
    bbox: BoundingBox


class DetectionFrame(BaseModel):
    type: str = "detections"
    timestamp: float
    fps: float
    objects: list[Detection] = []


# ── Motor Control ───────────────────────────────────────

class DriveCommand(BaseModel):
    left: int = Field(ge=-100, le=100, description="Left motor speed (-100 to 100)")
    right: int = Field(ge=-100, le=100, description="Right motor speed (-100 to 100)")


class MotorStatus(BaseModel):
    uart_connected: bool
    mcu_responding: bool
    last_command: DriveCommand | None = None


# ── System ──────────────────────────────────────────────

class SystemHealth(BaseModel):
    cpu_temp_c: float | None = None
    npu_temp_c: float | None = None
    uptime_seconds: float
    fps: float
    inference_engine: str
    camera_backend: str
    network_mode: str


class ConfigUpdate(BaseModel):
    network_mode: str | None = None
    confidence_threshold: float | None = Field(None, ge=0.0, le=1.0)
    motor_enabled: bool | None = None
