# Object Detection on Raspberry Pi 5

Real-time object detection with YOLOv8 on Raspberry Pi 5 + Hailo AI Hat (26 TOPS). Web-based UI with live video stream, detection overlays, and motor control for smart vehicle integration.

## Hardware
- **Raspberry Pi 5** (8 GB RAM)
- **Hailo AI Hat** (26 TOPS NPU)
- **Camera**: USB webcam (dev) / Pi Camera Module 3 (target)
- **MCU**: STM32F446RE
- **Motor Driver**: TB6612FNG / DRV8871
- **Motors**: 2× 12V DC (333 RPM)

## Quick Start

### Prerequisites
- Raspberry Pi 5 running Raspberry Pi OS (64-bit, Bookworm)
- Docker (recommended) or Python 3.11+

### Docker (Recommended)
```bash
cd raspi/server
docker compose up -d
```

### Hailo NPU (bare-metal, recommended for the AI Hat)
Runs the server + GStreamer inference pipeline inside the Pi's `venv_hailo_apps`
(hailo-apps 26.03, Trixie). Full setup in [hailo-setup.md](raspi/docs/hailo-setup.md).

```bash
cd ~/hailo-apps && source setup_env.sh          # activates venv_hailo_apps
cd ~/smart-vehicle
pip install -r raspi/server/requirements.txt
pip install -e raspi/hailo-layer

cd raspi/server
cp .env.example .env                            # set INFERENCE_ENGINE=hailo
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Standalone pipeline check (no server): `hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30`

### Bare-Metal (ONNX / CPU)
```bash
cd raspi/server
bash scripts/setup.sh
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access
Open `http://<raspberry-pi-ip>:8000` in any browser on the same network.

## Project Structure
```
├── raspi/           # Raspberry Pi application
│   ├── frontend/    # React + Vite + Tailwind SPA
│   ├── server/      # FastAPI Python backend
│   └── docs/        # Setup & configuration guides
├── firmware/        # STM32 motor control (Phase 6)
└── PLAN.md          # Full architecture document
```

## Documentation
- [Architecture Plan](PLAN.md) — full system design
- [Hailo AI Hat Setup](raspi/docs/hailo-setup.md)
- [Model Compilation](raspi/docs/model-compilation.md)
- [Networking (LAN + Hotspot)](raspi/docs/networking.md)

## Development Phases
1. **Foundation** — Camera streaming + web UI
2. **Inference** — YOLOv8 ONNX CPU inference
3. **AI Hat** — Hailo NPU acceleration (hailo-layer Option B package) ✅
4. **Motor Control** — UART + joystick control
5. **Polish** — Hotspot, monitoring, UI refinement
6. **Vehicle** — STM32 firmware + physical integration
