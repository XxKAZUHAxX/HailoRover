"""Motor control service — joystick mapping + differential drive + UART dispatch."""

from __future__ import annotations

import logging

from app.config import settings
from app.hal.uart_hal import UARTMotorController
from app.models.schemas import DriveCommand, MotorStatus

logger = logging.getLogger(__name__)


class MotorService:
    """Translates joystick coordinates into motor commands via UART."""

    def __init__(self) -> None:
        self._uart = UARTMotorController()
        self._last_command: DriveCommand | None = None

    def initialize(self) -> None:
        """Open UART and verify communication with the STM32."""
        if not settings.motor_enabled:
            logger.info("Motor service disabled (motor_enabled=False)")
            return
        self._uart.open()

    def drive(self, forward: float, turn: float) -> None:
        """
        Apply joystick axes to differential drive.

        Args:
            forward: -1.0 (full reverse) to 1.0 (full forward), joystick 1 Y-axis
            turn:    -1.0 (full left) to 1.0 (full right), joystick 2 X-axis
        """
        fwd = int(forward * 100)
        trn = int(turn * 100)

        left_speed = max(-100, min(100, fwd + trn))
        right_speed = max(-100, min(100, fwd - trn))

        self._last_command = DriveCommand(left=left_speed, right=right_speed)
        self._uart.drive(left_speed, right_speed)

    def stop(self) -> None:
        """Coast stop — motors free-run."""
        self._uart.stop()
        if self._last_command:
            self._last_command = DriveCommand(left=0, right=0)

    def brake(self) -> None:
        """Active brake — short motor leads."""
        self._uart.brake()
        if self._last_command:
            self._last_command = DriveCommand(left=0, right=0)

    @property
    def status(self) -> MotorStatus:
        return MotorStatus(
            uart_connected=self._uart.is_connected,
            mcu_responding=self._uart.ping() if self._uart.is_connected else False,
            last_command=self._last_command,
        )

    def shutdown(self) -> None:
        """Stop motors and close UART."""
        self._uart.stop()
        self._uart.close()


# Module-level singleton
motor_service = MotorService()
