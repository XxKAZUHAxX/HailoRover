#!/usr/bin/env bash
# ── Bare-metal setup script for Raspberry Pi 5 ──
# Usage: bash scripts/setup.sh
set -euo pipefail

echo "══╡ HailoRover Server — Bare-Metal Setup ╞══"

# ── System packages ──────────────────────────────────────
echo "[1/4] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    libglib2.0-0t64

# ── Python virtual environment ───────────────────────────
echo "[2/4] Creating Python virtual environment..."
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── Python packages ──────────────────────────────────────
echo "[3/4] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# ── Frontend build (if Node.js is available) ─────────────
echo "[4/4] Checking frontend..."
FRONTEND_DIR="../frontend"
FRONTEND_DIST="frontend-dist"
if [ -d "$FRONTEND_DIR" ] && command -v npm &> /dev/null; then
    echo "Building frontend..."
    cd "$FRONTEND_DIR"
    npm ci
    npm run build
    cd -
    # Copy build output
    mkdir -p "$FRONTEND_DIST"
    cp -r "$FRONTEND_DIR/dist/"* "$FRONTEND_DIST/"
    echo "Frontend built → $FRONTEND_DIST/"
else
    echo "⚠  Frontend not built (install Node.js 20+ and run: cd ../frontend && npm ci && npm run build)"
fi

# ── Model download placeholder ───────────────────────────
echo ""
echo "══╡ Setup Complete ╞══"
echo ""
echo "Next steps:"
echo "  1. Activate venv and download YOLOv8n ONNX model:"
echo "     source venv/bin/activate"
echo "     pip install ultralytics"
echo "     python -c \"from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='onnx')\""
echo "     mv yolov8n.onnx models/"
echo "     deactivate"
echo ""
echo "  2. Start the server:"
echo "     source venv/bin/activate"
echo "     uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  3. Open http://<raspi-ip>:8000 in your browser"
