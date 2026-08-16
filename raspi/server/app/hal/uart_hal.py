"""UART communication with STM32 motor controller.

Binary protocol:
    [START 0xAA] [CMD 1B] [LEN 1B] [PAYLOAD N bytes] [CRC8 1B]

Commands:
    0x01 DRIVE  [left_speed int8] [right_speed int8]
    0x02 STOP   (no payload)
    0x03 PING   (no payload) → response: [status uint8]
    0x04 BRAKE  (no payload)
"""

from __future__ import annotations

import logging
import time

from app.config import settings

logger = logging.getLogger(__name__)

# Protocol constants
START_BYTE = 0xAA

CMD_DRIVE = 0x01
CMD_STOP = 0x02
CMD_PING = 0x03
CMD_BRAKE = 0x04

CRC8_POLY = 0x07
CRC8_INIT = 0x00


def _crc8(data: bytes) -> int:
    """Compute CRC-8-ATM on the given data."""
    crc = CRC8_INIT
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ CRC8_POLY) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def _build_packet(command: int, payload: bytes = b"") -> bytes:
    """Build a protocol packet."""
    length = len(payload)
    header = bytes([START_BYTE, command, length])
    crc = _crc8(header + payload)
    return header + payload + bytes([crc])


class UARTMotorController:
    """Manages UART communication with the STM32 motor controller."""

    def __init__(self) -> None:
        self._serial = None
        self._connected = False

    def open(self) -> None:
        """Open the UART connection to the STM32."""
        if not settings.motor_enabled:
            logger.info("Motor control disabled — skipping UART init")
            return
        try:
            import serial
        except ImportError:
            raise RuntimeError("pyserial not installed")
        try:
            self._serial = serial.Serial(
                port=settings.uart_port,
                baudrate=settings.uart_baud,
                timeout=0.1,
            )
            self._connected = True
            logger.info("UART opened on %s @ %d baud", settings.uart_port, settings.uart_baud)
        except Exception as e:
            logger.warning("Failed to open UART: %s — motor control unavailable", e)
            self._connected = False

    def close(self) -> None:
        """Close the UART connection."""
        if self._serial is not None:
            self._serial.close()
        self._connected = False

    def drive(self, left_speed: int, right_speed: int) -> None:
        """Send motor speed command. Values: -100 to 100."""
        if not self._connected:
            logger.debug("UART not connected — drive command dropped")
            return
        left = max(-100, min(100, left_speed))
        right = max(-100, min(100, right_speed))
        packet = _build_packet(CMD_DRIVE, bytes([left & 0xFF, right & 0xFF]))
        self._serial.write(packet)  # type: ignore[union-attr]
        logger.debug("DRIVE sent: L=%d R=%d", left, right)

    def stop(self) -> None:
        """Send immediate stop (coast) command."""
        if not self._connected:
            return
        packet = _build_packet(CMD_STOP)
        self._serial.write(packet)  # type: ignore[union-attr]
        logger.debug("STOP sent")

    def brake(self) -> None:
        """Send active brake command."""
        if not self._connected:
            return
        packet = _build_packet(CMD_BRAKE)
        self._serial.write(packet)  # type: ignore[union-attr]
        logger.debug("BRAKE sent")

    def ping(self) -> bool:
        """Ping the STM32. Returns True if it responds."""
        if not self._connected or self._serial is None:
            return False
        packet = _build_packet(CMD_PING)
        self._serial.write(packet)
        time.sleep(0.05)  # wait for MCU to respond
        if self._serial.in_waiting >= 1:
            response = self._serial.read(1)
            return response[0] == 0x00  # status OK
        return False

    @property
    def is_connected(self) -> bool:
        return self._connected
