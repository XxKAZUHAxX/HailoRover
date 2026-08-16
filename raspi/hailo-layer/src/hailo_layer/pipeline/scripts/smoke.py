"""Standalone pipeline smoke test — runs the detection pipeline N seconds without the server.

Usage (on the Pi, inside venv_hailo_apps):
    hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30
"""

from __future__ import annotations

import argparse
import sys
import time

from hailo_layer.config import PipelineOptions
from hailo_layer.domain.frame_queue import FrameQueue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hailo detection pipeline smoke test")
    parser.add_argument("--hef-path", default=None, help="HEF name or path (default: per-arch default)")
    parser.add_argument("--labels-json", default=None, help="Labels JSON for hailofilter (default: COCO-80)")
    parser.add_argument("--arch", default=None, help="hailo8 | hailo8l | hailo10h (default: auto-detect)")
    parser.add_argument("--input", default="/dev/video0", help="v4l2 device, 'usb', or 'rpi'")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--frame-rate", type=int, default=30)
    parser.add_argument("--run-time", type=float, default=30.0, help="seconds to run")
    args = parser.parse_args(argv)

    from hailo_layer.pipeline.runner import PipelineRunner, check_hailo_apps_version

    check_hailo_apps_version()

    options = PipelineOptions(
        hef_path=args.hef_path,
        labels_json=args.labels_json,
        arch=args.arch,
        input_source=args.input,
        width=args.width,
        height=args.height,
        frame_rate=args.frame_rate,
    )
    queue = FrameQueue(maxsize=2)
    runner = PipelineRunner(options, queue)
    print(
        f"Starting pipeline: input={args.input} hef={args.hef_path or 'auto'} "
        f"run-time={args.run_time}s"
    )
    runner.start()
    runner.wait_ready()
    print("Pipeline running — collecting frames...")

    t0 = time.monotonic()
    frame_count = 0
    det_count = 0
    while time.monotonic() - t0 < args.run_time:
        result = queue.pop_nowait()
        if result is None:
            time.sleep(0.001)
            continue
        frame_count += 1
        det_count += len(result.detections)
        if frame_count % 30 == 0:
            shown = [(d.label, round(d.confidence, 2)) for d in result.detections[:5]]
            print(f"  frame {frame_count}: latency={result.latency_ms:.1f}ms detections={shown}")

    elapsed = time.monotonic() - t0
    runner.stop()
    print(
        f"SMOKE OK: {frame_count} frames in {elapsed:.1f}s "
        f"({frame_count / elapsed:.1f} fps), {det_count} detections total"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
