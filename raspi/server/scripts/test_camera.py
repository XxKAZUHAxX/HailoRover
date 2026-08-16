#!/usr/bin/env python3
"""Quick camera validation — captures frames and reports stats.

Usage:
    python scripts/test_camera.py [--backend v4l2|libcamera] [--device /dev/video0]
"""

from __future__ import annotations

import argparse
import os
import time
import sys
from pathlib import Path

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np


def test_camera(device: str = "/dev/video0", num_frames: int = 100) -> None:
    """Open camera, capture frames, print diagnostics."""
    print(f"Opening camera: {device}")
    cap = cv2.VideoCapture(device)

    # Try MJPEG codec for higher FPS (must be set before resolution)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("ERROR: Failed to open camera")
        sys.exit(1)

    actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4))

    print(f"Resolution: {actual_w:.0f}x{actual_h:.0f}")
    print(f"Target FPS: {actual_fps:.0f}")
    print(f"Codec: {fourcc_str}")
    print(f"Capturing {num_frames} frames...")

    start = time.perf_counter()
    frames = []
    for i in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            print(f"ERROR: Frame {i} read failed")
            break
        frames.append(frame)

    elapsed = time.perf_counter() - start
    cap.release()

    if frames:
        avg_fps = len(frames) / elapsed
        avg_size_kb = sum(f.nbytes for f in frames) / len(frames) / 1024
        print(f"\n══╡ Results ╞══")
        print(f"Frames captured: {len(frames)}/{num_frames}")
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Measured FPS: {avg_fps:.1f}")
        print(f"Avg frame size: {avg_size_kb:.1f} KB")
        print(f"Frame shape: {frames[0].shape}")
        print(f"Frame dtype: {frames[0].dtype}")

        # Show first frame (only if a display is available)
        if "DISPLAY" in os.environ or os.environ.get("WAYLAND_DISPLAY"):
            cv2.imshow("Camera Test — Press any key to close", frames[0])
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            # Headless: save frame to disk instead
            out_path = Path("camera_test_frame.jpg")
            cv2.imwrite(str(out_path), frames[0])
            print(f"Headless mode — first frame saved to {out_path}")

        if avg_fps < 15:
            print("\n⚠  WARNING: Low FPS detected. Try:")
            print("  - Using MJPEG codec (already attempted)")
            print("  - Reducing resolution")
            print("  - Checking USB bandwidth (use a USB 3.0 port)")
    else:
        print("ERROR: No frames captured")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Camera validation utility")
    parser.add_argument("--device", default="/dev/video0", help="Camera device path")
    parser.add_argument("--frames", type=int, default=100, help="Number of frames to capture")
    args = parser.parse_args()

    test_camera(device=args.device, num_frames=args.frames)
