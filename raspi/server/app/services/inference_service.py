"""YOLOv8 object detection — CPU (ONNX) and NPU (Hailo) paths."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# COCO 2017 class names (80 classes)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
]


class ONNXInferenceEngine:
    """YOLOv8 inference using ONNX Runtime (CPU fallback)."""

    # YOLOv8 input size
    INPUT_SIZE = (640, 640)

    def __init__(self, model_path: str) -> None:
        self.model_path = Path(model_path)
        self._session: Any = None
        self._input_name: str = ""
        self._output_name: str = ""

    def initialize(self) -> None:
        """Load the ONNX model."""
        import onnxruntime as ort

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        providers = ["CPUExecutionProvider"]
        self._session = ort.InferenceSession(
            str(self.model_path),
            providers=providers,
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name
        logger.info("ONNX model loaded: %s", self.model_path)

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Resize, normalize, and convert to NCHW for YOLOv8."""
        img = cv2.resize(frame, self.INPUT_SIZE)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        # HWC → NCHW
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img

    def _postprocess(
        self,
        outputs: np.ndarray,
        original_shape: tuple[int, int],
    ) -> list[dict[str, Any]]:
        """Parse YOLOv8 output, apply NMS, scale to original image coords."""
        orig_h, orig_w = original_shape
        scale_x = orig_w / self.INPUT_SIZE[0]
        scale_y = orig_h / self.INPUT_SIZE[1]

        # YOLOv8 output: [1, 84, 8400] → transpose to [8400, 84]
        predictions = np.squeeze(outputs[0]).T  # shape: [8400, 84]

        # Filter by confidence
        scores = np.max(predictions[:, 4:], axis=1)
        class_ids = np.argmax(predictions[:, 4:], axis=1)
        mask = scores > settings.confidence_threshold

        filtered = predictions[mask]
        scores = scores[mask]
        class_ids = class_ids[mask]

        if len(filtered) == 0:
            return []

        # Extract boxes (cx, cy, w, h) → (x1, y1, x2, y2)
        boxes_xywh = filtered[:, :4]
        cx, cy, w, h = boxes_xywh[:, 0], boxes_xywh[:, 1], boxes_xywh[:, 2], boxes_xywh[:, 3]
        x1 = (cx - w / 2) * scale_x
        y1 = (cy - h / 2) * scale_y
        x2 = (cx + w / 2) * scale_x
        y2 = (cy + h / 2) * scale_y
        boxes = np.stack([x1, y1, x2, y2], axis=1)

        # NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.astype(np.float32).tolist(),
            scores.tolist(),
            settings.confidence_threshold,
            settings.iou_threshold,
        )

        results = []
        for i in indices:
            idx = i if isinstance(i, int) else i[0]
            x1_b, y1_b, x2_b, y2_b = boxes[idx]
            results.append({
                "class": COCO_CLASSES[int(class_ids[idx])] if int(class_ids[idx]) < len(COCO_CLASSES) else "unknown",
                "class_id": int(class_ids[idx]),
                "confidence": round(float(scores[idx]), 4),
                "bbox": {
                    "x": int(x1_b),
                    "y": int(y1_b),
                    "width": int(x2_b - x1_b),
                    "height": int(y2_b - y1_b),
                },
            })
        return results

    def infer(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Run inference on a single frame."""
        if self._session is None:
            return []
        input_tensor = self._preprocess(frame)
        outputs = self._session.run([self._output_name], {self._input_name: input_tensor})
        return self._postprocess(outputs[0], frame.shape[:2])

    def shutdown(self) -> None:
        """Release ONNX session resources."""
        self._session = None


class InferenceService:
    """Top-level inference service — selects engine based on config."""

    def __init__(self) -> None:
        self._engine: ONNXInferenceEngine | Any = None
        self._inference_time_ms = 0.0

    def initialize(self) -> None:
        """Initialize the configured inference engine."""
        engine_type = settings.inference_engine
        if engine_type == "hailo":
            from app.hal.hailo_hal import HailoRuntime
            self._engine = HailoRuntime(str(settings.model_path_resolved))
            logger.info("Inference engine: Hailo NPU")
        else:
            self._engine = ONNXInferenceEngine(str(settings.model_path_resolved))
            logger.info("Inference engine: ONNX (CPU)")

        self._engine.initialize()

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Run detection on a frame. Returns list of detection dicts."""
        t0 = time.perf_counter()
        results = self._engine.infer(frame)
        self._inference_time_ms = (time.perf_counter() - t0) * 1000
        return results

    @property
    def inference_time_ms(self) -> float:
        return self._inference_time_ms

    @property
    def is_initialized(self) -> bool:
        return self._engine is not None

    def shutdown(self) -> None:
        if self._engine is not None:
            self._engine.shutdown()
            self._engine = None


# Module-level singleton
inference_service = InferenceService()
