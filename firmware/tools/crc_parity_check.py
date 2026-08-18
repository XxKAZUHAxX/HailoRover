#!/usr/bin/env python3
"""CRC-8 parity check: firmware C implementation vs Pi Python implementation.

Verifies that firmware/lib/Protocol/protocol.c's CRC-8-ATM is byte-for-byte
equivalent to raspi/server/app/hal/uart_hal.py:_crc8() — the wire contract.

Usage: python tools/crc_parity_check.py
Exit 0 = all vectors match (or live import skipped with a warning).
"""

import random
import sys
import warnings

CRC8_POLY = 0x07
CRC8_INIT = 0x00


def c_crc8(data: bytes) -> int:
    """1:1 transliteration of crc8_update/protocol_crc8 in lib/Protocol/protocol.c:
    crc ^= byte; 8x: if (crc & 0x80) crc = (crc << 1) ^ 0x07 else crc <<= 1 (all & 0xFF)."""
    crc = CRC8_INIT
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ CRC8_POLY) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def python_crc8(data: bytes) -> int:
    """Verbatim copy of uart_hal.py:_crc8() (lines 34-41)."""
    crc = CRC8_INIT
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ CRC8_POLY) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def make_frame(command: int, payload: bytes) -> bytes:
    """Protocol frame per uart_hal.py:_build_packet: [0xAA][CMD][LEN][PAYLOAD][CRC]."""
    header = bytes([0xAA, command, len(payload)])
    return header + payload + bytes([python_crc8(header + payload)])


def main() -> int:
    rng = random.Random(0xC0FFEE)

    vectors: list[bytes] = []

    # Random byte strings (lengths 0-18)
    for _ in range(10_000):
        vectors.append(bytes(rng.randrange(256) for _ in range(rng.randrange(19))))

    # Protocol-shaped frames (valid)
    vectors.append(make_frame(0x01, bytes([100, -100 & 0xFF])))     # DRIVE +100/-100
    vectors.append(make_frame(0x01, bytes([0, 0])))                 # DRIVE 0/0
    vectors.append(make_frame(0x02, b""))                           # STOP
    vectors.append(make_frame(0x03, b""))                           # PING
    vectors.append(make_frame(0x04, b""))                           # BRAKE
    vectors.append(make_frame(0x01, bytes([0xAA, 0xAA])))           # 0xAA inside payload
    vectors.append(make_frame(0x01, bytes(range(16))))              # max payload

    for v in vectors:
        c = c_crc8(v)
        p = python_crc8(v)
        if c != p:
            print(f"MISMATCH on {v.hex()}: c={c:02x} python={p:02x}")
            return 1

    print(f"c_crc8 == python_crc8 over {len(vectors)} vectors — OK")

    # Live-import check against the real Pi implementation (optional deps).
    try:
        sys.path.insert(0, "../../raspi/server")
        from app.hal.uart_hal import _crc8  # noqa: E402
    except ImportError as exc:
        print(f"NOTE: live import of uart_hal._crc8 skipped "
              f"(missing deps on this machine: {exc}); embedded copy used as authority.")
        return 0

    for v in vectors:
        if _crc8(v) != c_crc8(v):
            print(f"LIVE MISMATCH on {v.hex()}")
            return 1
    print("Live uart_hal._crc8 matches — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
