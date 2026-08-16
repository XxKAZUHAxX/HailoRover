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

### Bare-Metal
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
3. **AI Hat** — Hailo NPU acceleration
4. **Motor Control** — UART + joystick control
5. **Polish** — Hotspot, monitoring, UI refinement
6. **Vehicle** — STM32 firmware + physical integration
