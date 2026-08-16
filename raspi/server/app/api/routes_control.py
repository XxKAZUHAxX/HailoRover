"""REST endpoints for motor control (differential drive via dual joystick)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import DriveCommand, MotorStatus
from app.services.motor_service import motor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/control", tags=["control"])


@router.post("/drive", response_model=MotorStatus)
async def set_motor_speeds(cmd: DriveCommand) -> MotorStatus:
    """Set individual motor speeds (-100 to 100)."""
    motor_service.drive(cmd.left / 100.0, 0.0)
    # Patch: convert raw left/right into differential for the service
    # This endpoint receives direct left/right speeds
    motor_service._uart.drive(cmd.left, cmd.right)
    return motor_service.status


@router.post("/joystick", response_model=MotorStatus)
async def joystick_control(forward: float = 0.0, turn: float = 0.0) -> MotorStatus:
    """
    Differential drive via dual joystick axes.

    - **forward**: -1.0 (full reverse) to 1.0 (full forward)
    - **turn**: -1.0 (full left) to 1.0 (full right)
    """
    motor_service.drive(forward, turn)
    return motor_service.status


@router.post("/stop", response_model=MotorStatus)
async def stop_motors() -> MotorStatus:
    """Immediate coast stop."""
    motor_service.stop()
    return motor_service.status


@router.post("/brake", response_model=MotorStatus)
async def brake_motors() -> MotorStatus:
    """Active braking."""
    motor_service.brake()
    return motor_service.status


@router.get("/status", response_model=MotorStatus)
async def motor_status() -> MotorStatus:
    """Get UART link and MCU health status."""
    return motor_service.status
