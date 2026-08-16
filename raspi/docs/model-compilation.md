# Model Compilation Guide — YOLOv8 → Hailo .hef

## Overview

The path from a trained YOLO model to running on the Hailo NPU involves three stages:

```
YOLOv8 .pt  ──[export]──▶  ONNX  ──[hailo DFC]──▶  .hef  ──[HailoRT]──▶  NPU
```

The `.hef` (Hailo Executable File) is a compiled binary optimized for the Hailo-8L architecture: INT8 quantized, layer-fused, and memory-mapped for the NPU.

---

## Stage 1: Export YOLOv8 to ONNX

```bash
# Install ultralytics
pip install ultralytics

# Download and export YOLOv8n (nano — fastest, lowest accuracy)
python -c "
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.export(format='onnx', imgsz=640, simplify=True, opset=12)
"

# Or use the project script:
python scripts/compile_model.py --weights yolov8n.pt --output models/yolov8n.onnx --onnx-only
```

Model size comparison:
| Variant | ONNX Size | Accuracy (mAP50) | Speed on Hailo-8L |
|---|---|---|---|
| YOLOv8n | ~6 MB | 37.3 | ~40+ FPS |
| YOLOv8s | ~22 MB | 44.9 | ~30 FPS |
| YOLOv8m | ~50 MB | 50.2 | ~20 FPS |

---

## Stage 2: Compile ONNX to Hailo .hef

This requires the **Hailo Dataflow Compiler (DFC)**, available in two forms:

### Option A: Hailo Model Zoo (EASIEST)

The Hailo Model Zoo provides pre-compiled .hef files for common models:

```bash
git clone https://github.com/hailo-ai/hailo_model_zoo.git
cd hailo_model_zoo

# List available YOLO models
python hailo_model_zoo/main.py models --filter yolov8

# Download a pre-compiled model
python hailo_model_zoo/main.py download yolov8s
```

### Option B: Manual Compilation with DFC

For custom-trained models, you need the full DFC:

```bash
pip install hailo-sdk-client

python scripts/compile_model.py --weights yolov8s.pt --output models/yolov8s.hef
```

The compilation script handles:
1. ONNX parsing and graph optimization
2. INT8 quantization (requires calibration dataset — ~100 images)
3. Resource allocation and layer fusion
4. .hef binary generation

---

## Stage 3: Load and Run

Update your `.env`:
```
INFERENCE_ENGINE=hailo
MODEL_PATH=models/yolov8s.hef
```

Restart the server — the Hailo HAL in `hal/hailo_hal.py` will load the .hef and route inference to the NPU.

---

## CPU vs NPU Performance Reference

| Setup | Model | FPS | Power |
|---|---|---|---|
| RPi 5 CPU | YOLOv8n ONNX | ~8-12 FPS | ~10W |
| RPi 5 + Hailo-8L | YOLOv8n .hef | ~40+ FPS | ~8W |
| RPi 5 + Hailo-8L | YOLOv8s .hef | ~30 FPS | ~8W |

---

## Custom Dataset Training (Future)

When you want to detect custom objects beyond COCO classes:

```bash
# Train on your custom dataset
yolo detect train \
    data=datasets/custom/data.yaml \
    model=yolov8s.pt \
    epochs=100 \
    imgsz=640

# Export trained model
yolo export model=runs/detect/train/weights/best.pt format=onnx

# Compile for Hailo
python scripts/compile_model.py \
    --weights runs/detect/train/weights/best.pt \
    --output models/custom_yolov8s.hef
```
