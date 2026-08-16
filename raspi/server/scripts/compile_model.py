#!/usr/bin/env python3
"""
YOLOv8 → ONNX → Hailo .hef Compilation Pipeline

This script automates the model export and compilation workflow for the
Hailo AI Hat. Run this ONCE to produce the .hef file, then the server
loads it at startup.

Prerequisites:
    - Hailo Dataflow Compiler installed (see raspi/docs/hailo-setup.md)
    - ultralytics installed: pip install ultralytics
    - A trained YOLOv8 .pt weights file

Usage:
    python scripts/compile_model.py --weights yolov8s.pt --output models/yolov8s.hef
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def export_to_onnx(weights_path: Path, output_dir: Path) -> Path:
    """Export YOLOv8 PyTorch model to ONNX format."""
    logger.info("Exporting %s → ONNX...", weights_path.name)
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    model = YOLO(str(weights_path))
    onnx_path = output_dir / f"{weights_path.stem}.onnx"
    model.export(format="onnx", imgsz=640, simplify=True)
    logger.info("ONNX exported: %s", onnx_path)
    return onnx_path


def compile_for_hailo(onnx_path: Path, output_path: Path) -> Path:
    """
    Compile ONNX model to Hailo .hef format.

    This uses the Hailo Dataflow Compiler (DFC) toolchain:
      1. Parse ONNX → Hailo internal representation
      2. Quantize to INT8
      3. Compile to .hef binary for Hailo-8L
    """
    logger.info("Compiling %s → Hailo .hef...", onnx_path.name)
    logger.warning(
        "Hailo compilation is NOT YET IMPLEMENTED — requires Hailo DFC installed on the system.\n"
        "See raspi/docs/model-compilation.md for the full manual workflow."
    )

    # ── Placeholder: real Hailo DFC pipeline ─────────────────
    # When Hailo DFC is available, the flow is:
    #
    # from hailo_sdk_client import ClientRunner
    #
    # runner = ClientRunner(hw_arch="hailo8l")
    # hn, npz = runner.translate_onnx_model(
    #     onnx_path, "yolov8s", start_node_names=["images"],
    #     end_node_names=["output0"]
    # )
    # runner.quantize(calib_dataset, optimization_level=3)
    # runner.compile()
    # runner.save_hef(str(output_path))
    # ─────────────────────────────────────────────────────────

    logger.info("Hailo compilation placeholder — returning ONNX path as-is")
    return onnx_path  # Placeholder


def main() -> None:
    parser = argparse.ArgumentParser(description="YOLOv8 → Hailo .hef compilation")
    parser.add_argument("--weights", required=True, help="Path to YOLOv8 .pt weights")
    parser.add_argument("--output", required=True, help="Output .hef path")
    parser.add_argument("--onnx-only", action="store_true", help="Stop after ONNX export (skip Hailo)")
    args = parser.parse_args()

    weights_path = Path(args.weights)
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if not weights_path.exists():
        logger.error("Weights file not found: %s", weights_path)
        sys.exit(1)

    # Step 1: PyTorch → ONNX
    onnx_path = export_to_onnx(weights_path, output_dir)

    if args.onnx_only:
        logger.info("Done (ONNX only). Output: %s", onnx_path)
        return

    # Step 2: ONNX → Hailo .hef
    hef_path = compile_for_hailo(onnx_path, output_path)
    logger.info("Done. Output: %s", hef_path)


if __name__ == "__main__":
    main()
