# Architecture Plan — Object Detection on Raspberry Pi 5

## Overview

Real-time object detection system on Raspberry Pi 5 with Hailo AI Hat (26 TOPS NPU). Serves a web application over the local network for live video streaming with detection overlays and motor control via dual analog joysticks. Future integration with STM32F446RE for DC motor control on a smart vehicle platform.

---

## Hardware

| Component | Model | Purpose |
|---|---|---|
| SBC | Raspberry Pi 5 (8 GB RAM) | Main compute, web server |
| NPU | Hailo AI Hat (26 TOPS) | Real-time YOLO inference |
| Camera (current) | USB Webcam (V4L2) | Development camera |
| Camera (future) | Raspberry Pi Camera Module 3 | Production camera |
| MCU | STM32F446RE (ARM Cortex-M4) | Real-time motor control |
| Motor Driver | TB6612FNG / DRV8871 | Dual H-bridge, 2x 12V DC motors |
| Motors | 2x 12V DC (333 RPM after gearbox) | Differential drive |

---

## Software Architecture

### Layer Stack

```
┌────────────────────────────────────────────────┐
│  React SPA (TypeScript + Vite + Tailwind CSS)   │
│  - Canvas-based video + bbox overlay            │
│  - Dual analog joysticks (touch + mouse)        │
│  - Detection stats & system health panel        │
├────────────────────────────────────────────────┤
│  FastAPI Server (Python 3.11+ Async)            │
│  - WebSocket: MJPEG frames + detection JSON     │
│  - REST: motor control, system status           │
│  - Static file serving (React build output)     │
├────────────────────────────────────────────────┤
│  Service Layer                                  │
│  - CameraService (V4L2 / libcamera abstraction) │
│  - InferenceService (YOLOv8 → HailoRT / ONNX)  │
│  - MotorService (UART → STM32 command builder)  │
│  - StreamService (MJPEG encode + frame mgmt)    │
├────────────────────────────────────────────────┤
│  Hardware Abstraction Layer (HAL)               │
│  - CameraHAL (USB + MIPI CSI)                   │
│  - HailoHAL (hailo_layer pipeline facade)       │
│  - UARTHAL (pyserial → STM32)                   │
├────────────────────────────────────────────────┤
│  hailo_layer (Option B package, Pi-only parts)  │
│  - GStreamerDetectionApp subclass + callback    │
│  - PipelineRunner (dedicated pipeline thread)   │
├────────────────────────────────────────────────┤
│  OS: Raspberry Pi OS (64-bit, Trixie)           │
│  Runtime: bare-metal venv_hailo_apps (hailo)    │
│           or Docker (onnx/CPU path)             │
└────────────────────────────────────────────────┘
```

### Data Flow: Video + Detection Stream

```
Camera ─▶ CameraHAL ─▶ CameraService ─▶ StreamService ──WebSocket──▶ Browser Canvas
                          │                                           │
                     InferenceService                                  │
                     (HailoRT NPU)                                     │
                          │                                            │
                     Detection[] ──▶ StreamService ──WebSocket──▶ Bbox Overlay
```

Single WebSocket connection carries both frame JPEGs (binary frames) and detection JSON (text frames). Browser composites them on a `<canvas>` — server never touches pixels.

### Data Flow: Motor Control

```
Browser Joystick ──REST POST──▶ MotorService ─▶ UARTHAL ─▶ STM32 ─▶ TB6612 ─▶ Motors
```

---

## Network Architecture

### LAN Mode (default)
RPi connects to home router via WiFi/Ethernet. Any device on the same LAN accesses the UI at `http://<rpi-ip>:8000`.

### Hotspot Mode
RPi creates its own WiFi access point (`hostapd` + `dnsmasq`). The vehicle is self-contained — no router needed. Toggle between modes via configuration.

---

## Communication Protocol: RPi ↔ STM32

### Physical Layer
UART at 115200 baud, 8N1, 3.3V logic (direct connection).

### Packet Format

```
┌──────────┬──────────┬──────────┬───────────────────┬──────────┐
│ START    │ CMD      │ LEN      │ PAYLOAD           │ CRC8     │
│ 0xAA     │ 1 byte   │ 1 byte   │ 0–255 bytes       │ 1 byte   │
└──────────┴──────────┴──────────┴───────────────────┴──────────┘
```

### Commands

| CMD | Name | Payload | Response | Description |
|---|---|---|---|---|
| `0x01` | DRIVE | `[left_speed int8] [right_speed int8]` | ACK/NACK | Set motor speeds (-100 to +100). Positive = forward on left motor. |
| `0x02` | STOP | none | ACK/NACK | Immediate motor stop (coast). |
| `0x03` | PING | none | `[status uint8]` | Health check. Status: 0=OK, 1=fault. |
| `0x04` | BRAKE | none | ACK/NACK | Active braking (short motor leads). |

### Differential Drive Math (Server-Side)

```
Joystick 1 (forward/reverse):  forward = map(y_axis, [-1, 1], [-100, 100])
Joystick 2 (left/right):       turn    = map(x_axis, [-1, 1], [-100, 100])

left_speed  = clamp(forward + turn, -100, 100)
right_speed = clamp(forward - turn, -100, 100)
```

---

## Inference Pipeline

### Phase 1: CPU Fallback (development, no AI Hat)
```
YOLOv8n (ONNX) → ONNX Runtime → CPU inference
Expected: ~10 FPS on RPi 5 CPU
```

### Phase 2: NPU Accelerated (with AI Hat)
```
v4l2src → hailo-apps GStreamer pipeline (hailonet + hailofilter C++ NMS)
       → handoff callback → FrameQueue → StreamService → WebSocket
Expected: ~30 FPS on Hailo-8L (yolov8m HEF, NMS compiled-in)
```

### Model Compilation Workflow
1. Export trained/fine-tuned YOLOv8 to ONNX
2. Parse ONNX with Hailo DFC (`hailo_model_optimizer`)
3. Quantize to INT8
4. Compile to `.hef` binary
5. Load with HailoRT Python API at runtime

Documented in `raspi/docs/model-compilation.md`.

---

## Project Structure

```
root/
├── raspi/                          # Raspberry Pi application
│   ├── frontend/                   # React + Vite + Tailwind SPA
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── VideoStream.tsx      # Canvas + WebSocket renderer
│   │   │   │   ├── DualJoystick.tsx     # Touch/mouse dual joysticks
│   │   │   │   ├── DetectionPanel.tsx   # Object counts & confidence
│   │   │   │   ├── SystemStatus.tsx     # CPU temp, NPU load, FPS
│   │   │   │   └── ControlBar.tsx       # Mode toggles, settings
│   │   │   ├── hooks/
│   │   │   │   ├── useWebSocket.ts      # WebSocket connection manager
│   │   │   │   └── useJoystick.ts       # Touch/mouse input handler
│   │   │   ├── lib/
│   │   │   │   ├── ws-client.ts         # WebSocket client logic
│   │   │   │   └── bbox-renderer.ts     # Canvas bounding box drawing
│   │   │   ├── types/
│   │   │   │   └── index.ts             # Shared TypeScript types
│   │   │   ├── App.tsx
│   │   │   └── main.tsx
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── postcss.config.js
│   ├── server/                     # FastAPI Python backend
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                  # FastAPI app factory + lifespan
│   │   │   ├── config.py                # Pydantic-settings config
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes_stream.py     # /ws/stream WebSocket endpoint
│   │   │   │   ├── routes_control.py    # /api/control/* REST endpoints
│   │   │   │   └── routes_system.py     # /api/system/* health endpoints
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── camera_service.py    # Camera lifecycle + frame capture
│   │   │   │   ├── inference_service.py # YOLO model loading + inference
│   │   │   │   ├── motor_service.py     # Motor command translation
│   │   │   │   └── stream_service.py    # Frame encoding + multiplexing
│   │   │   ├── hal/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── camera_hal.py        # V4L2 / libcamera backend
│   │   │   │   ├── hailo_hal.py         # HailoRT Python bindings
│   │   │   │   └── uart_hal.py          # pyserial UART interface
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       └── schemas.py           # Pydantic request/response models
│   │   ├── scripts/
│   │   │   ├── setup.sh                 # Bare-metal dependency installer
│   │   │   ├── compile_model.py         # YOLO → ONNX → Hailo .hef pipeline
│   │   │   └── test_camera.py           # Camera validation utility
│   │   ├── requirements.txt
│   │   ├── requirements-dev.txt
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── hailo-layer/                  # Option B inference package (depends on hailo-apps)
│   │   ├── pyproject.toml
│   │   ├── src/hailo_layer/
│   │   │   ├── types.py                 # BBox / Detection / FrameResult dataclasses
│   │   │   ├── config.py                # PipelineOptions
│   │   │   ├── domain/                  # pure Python: FrameQueue, conversions
│   │   │   └── pipeline/                # Pi-only: hailo_compat, parser, app, callback, runner
│   │   └── tests/                       # domain tests (pytest on Windows)
│   └── docs/
│       ├── hailo-setup.md               # Hailo stack setup (real stack: hailo-apps 26.03)
│       ├── model-compilation.md         # Step-by-step model export guide
│       └── networking.md                # LAN + hotspot configuration
├── firmware/                        # STM32 motor control (future)
│   ├── Core/
│   │   ├── Inc/
│   │   │   ├── main.h
│   │   │   ├── uart_protocol.h
│   │   │   └── motor_control.h
│   │   └── Src/
│   │       ├── main.c
│   │       ├── uart_protocol.c
│   │       └── motor_control.c
│   ├── Drivers/
│   └── CMakeLists.txt
├── PLAN.md
├── README.md
└── .gitignore
```

---

## API Design

### WebSocket: `/ws/stream`
Binary frame = JPEG image
Text frame = JSON detection array

```json
{
  "type": "detections",
  "timestamp": 1723471234.567,
  "fps": 29.8,
  "objects": [
    {
      "class": "person",
      "class_id": 0,
      "confidence": 0.92,
      "bbox": { "x": 120, "y": 80, "width": 200, "height": 350 }
    }
  ]
}
```

### REST: `/api/control`

| Method | Path | Body | Description |
|---|---|---|---|
| POST | `/api/control/drive` | `{ "left": -50, "right": 75 }` | Set motor speeds |
| POST | `/api/control/stop` | — | Coast stop |
| POST | `/api/control/brake` | — | Active brake |
| GET | `/api/control/status` | — | UART link health |

### REST: `/api/system`

| Method | Path | Description |
|---|---|---|
| GET | `/api/system/health` | CPU temp, NPU temp, uptime, FPS |
| GET | `/api/system/config` | Current config (network mode, model, etc.) |
| PATCH | `/api/system/config` | Update config |

---

## Key Design Decisions

### Why client-side bbox rendering?
Server encodes frames once (MJPEG) and sends detection as lightweight JSON. The browser composites them. This:
- Zero server CPU spent on drawing
- Detection data available for other UI (counts, alerts) without parsing frames
- Clean separation: stream is a stream, detections are data

### Why single WebSocket for both frames + detection?
One connection per client. Detection is synchronized to the frame it was inferred on. No timestamp reconciliation between separate connections. Browser WebSocket handles binary and text frames natively.

### Why UART binary protocol (not I²C or SPI)?
UART requires 2 wires, works over longer distances on a vehicle chassis, and the STM32F446RE has plenty of UART peripherals. 115200 bps is more than enough for ~100 Hz motor command updates.

### Why differential drive math on the server?
Keeps the STM32 firmware dead simple: receive two PWM duty values, apply them. All the control logic (joystick mapping, speed ramping, dead zones) lives in Python where it's easy to test and modify.

### Hailo Inference Layer (Option B)
Hailo inference is implemented as a **separate installable package** (`raspi/hailo-layer/`) that depends on hailo-apps rather than editing hailo-apps itself:

- **Pipeline takeover mode** — when `INFERENCE_ENGINE=hailo`, a `GStreamerDetectionApp` subclass runs camera + inference in a dedicated background thread (hailo-apps owns the camera; the server's `camera_service` is not started). The handoff callback pushes `FrameResult(BGR frame, detections, latency_ms)` into a drop-oldest `FrameQueue`; `stream_service` consumes it instead of `camera.read()` + `detect()`. The ONNX path is untouched and Docker stays CPU-only.
- **Layering** — `hailo_layer.types` / `hailo_layer.domain` are pure Python (no hailo/GStreamer imports; pytest on Windows). `hailo_layer.pipeline` is hailo-aware and imported only on the Pi.
- **Coupling policy** — the `hailo-apps/` clone in the repo root is reference-only (gitignored). Every hailo-apps import and the version range constants live in one file: `hailo_layer/pipeline/hailo_compat.py`. Upgrading hailo-apps = bump two constants, review that one file, rerun `hailo-smoke`.
- **Venv strategy** — the server runs inside `venv_hailo_apps` (Trixie, Python 3.13); server requirements + hailo-layer are pip-installed into it. `opencv-python` is replaced by `opencv-python-headless` (expected).
- **Thread lifecycle** — the GStreamer app is constructed and run in one daemon thread (GLib mainloop thread affinity). Embedded-hostile behaviors are neutralized: `signal.signal` call in the parent `__init__`, `sys.exit` at end of `run()`, `autovideosink` → `fakesink`, hailo's `init_logging(force=True)` handler wipe is restored.
- **Labels divergence** — hailo labels come from the HEF (COCO-80 built into the TAPPAS `.so` for yolov8\*); the ONNX engine keeps its hardcoded `COCO_CLASSES`. They agree for stock COCO models. Custom-label HEFs require `LABELS_JSON` (+ `COCO_CLASSES` update) in the same change.
- **NMS thresholds divergence** — hailo NMS is hardcoded 0.3/0.45 by `GStreamerDetectionApp`; `CONFIDENCE_THRESHOLD` / `IOU_THRESHOLD` apply to the ONNX engine only.

Version pairing matrix lives in `raspi/docs/hailo-setup.md` (hailo-apps 26.03.x ↔ HailoRT 4.23 ↔ TAPPAS 5.1 ↔ Trixie/Python 3.13).

---

## Development Phases

### Phase 1: Foundation (NOW)
- [ ] Project scaffolding + PLAN.md
- [ ] FastAPI server with health endpoints
- [ ] USB camera capture + MJPEG streaming
- [ ] React frontend with video display
- [ ] Docker + bare-metal setup scripts

### Phase 2: Inference
- [ ] YOLOv8 ONNX CPU inference
- [ ] Detection overlay on frontend
- [ ] Performance benchmarking (FPS, latency)

### Phase 3: AI Hat Integration
- [x] HailoRT driver + SDK installation
- [x] Model compilation pipeline
- [x] NPU-accelerated inference (hailo-layer Option B package + pipeline takeover)
- [ ] A/B performance comparison

### Phase 4: Motor Control
- [ ] UART HAL implementation
- [ ] Motor control REST API
- [ ] Dual joystick frontend component
- [ ] End-to-end test with STM32 + motors

### Phase 5: Networking & Polish
- [ ] Hotspot mode configuration
- [ ] System health monitoring
- [ ] UI/UX refinement
- [ ] Documentation completion

### Phase 6: Vehicle Integration
- [ ] STM32 firmware development
- [ ] Physical integration (mounting, wiring)
- [ ] Field testing

---

## Configuration
All runtime configuration via environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `CAMERA_BACKEND` | `v4l2` | `v4l2` (USB) or `libcamera` (MIPI) |
| `CAMERA_DEVICE` | `/dev/video0` | Camera device path |
| `CAMERA_WIDTH` | `640` | Frame width |
| `CAMERA_HEIGHT` | `480` | Frame height |
| `CAMERA_FPS` | `30` | Target capture FPS |
| `INFERENCE_ENGINE` | `onnx` | `onnx` (CPU) or `hailo` (NPU) |
| `MODEL_PATH` | `models/yolov8n.onnx` | Path to model file (ONNX engine) |
| `CONFIDENCE_THRESHOLD` | `0.5` | Minimum detection confidence (ONNX engine) |
| `HEF_PATH` | `yolov8m` | HEF name/path; auto-downloaded by hailo-apps |
| `LABELS_JSON` | — | Custom labels json for hailofilter (COCO default) |
| `HAILO_ARCH` | — | `hailo8` / `hailo8l` / `hailo10h` (auto-detect) |
| `HAILO_QUEUE_SIZE` | `2` | FrameQueue depth (drop-oldest) |
| `HAILO_WATCHDOG` | `false` | hailo-apps pipeline watchdog |
| `HAILO_STARTUP_TIMEOUT` | `60` | Seconds; first run may download the HEF |
| `UART_PORT` | `/dev/ttyAMA0` | STM32 UART device |
| `UART_BAUD` | `115200` | UART baud rate |
| `NETWORK_MODE` | `lan` | `lan` or `hotspot` |
| `SERVER_PORT` | `8000` | FastAPI listen port |
