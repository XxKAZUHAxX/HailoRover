#!/usr/bin/env python3
"""Read the Hailo AI HAT's on-chip temperature sensors (TS0/TS1).

Usage: python scripts/npu_temp.py   (inside the project venv — source setup.sh)

The chip has two internal temperature sensors; this prints both plus the
average. Uses the legacy hailo_platform binding — the newer `hailo` module
does not expose temperature.
"""

import sys

from hailo_platform import Device


def main() -> int:
    try:
        device = Device()
        info = device.control.get_chip_temperature()
    except Exception as e:
        print(f"Error accessing Hailo device: {e}")
        print("Is the venv active? Run: source setup.sh")
        return 1

    avg = (info.ts0_temperature + info.ts1_temperature) / 2
    print(f"Sensor 0: {info.ts0_temperature:.2f}°C")
    print(f"Sensor 1: {info.ts1_temperature:.2f}°C")
    print(f"Average : {avg:.2f}°C")
    return 0


if __name__ == "__main__":
    sys.exit(main())
