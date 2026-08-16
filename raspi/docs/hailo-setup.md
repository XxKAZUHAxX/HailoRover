# Hailo AI Hat Setup Guide

This guide covers the **actual stack in use** on the vehicle's Pi: Hailo AI HAT+ (Hailo-8L, 26 TOPS) on Raspberry Pi 5 with **hailo-apps** (successor of the deprecated `hailo-rpi5-examples`).

## Version pairing — do not drift

| Component | Version |
|---|---|
| hailo-apps | 26.03.x |
| HailoRT | 4.23.0 |
| TAPPAS (postprocess) | 5.1.0 |
| Raspberry Pi OS | Trixie (64-bit), Python 3.13 |
| venv | `venv_hailo_apps` (created by `install.sh`) |
| hailo-layer (this repo) | 0.1.x — requires hailo-apps `>=26.03.0,<26.04` |

Mixing versions breaks things in confusing ways — e.g. old infra tags with TAPPAS 5.1 fail the C++ postprocess compile (`'class HailoTensor' has no member named 'vstream_info'`).

---

## 1. Enable PCIe Gen 3

```bash
sudo nano /boot/firmware/config.txt
```

Add at the end:

```
# Enable PCIe Gen 3 for Hailo AI Hat
dtparam=pciex1_gen=3
```

Reboot, then verify:

```bash
sudo reboot
lspci | grep Hailo   # Expected: Hailo Technologies Ltd. Device ...
```

---

## 2. Install hailo-apps

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-apps.git
cd hailo-apps
sudo ./install.sh
```

What this does:

1. Installs HailoRT + TAPPAS system packages (apt)
2. Creates the virtual environment `venv_hailo_apps`
3. `pip install -e .` (hailo-apps is installed **editable** — its source is the clone)
4. Post-install (`hailo-post-install`): downloads ~1.5 GB of models to
   `/usr/local/hailo/resources` and compiles the C++ postprocess `.so` files to
   `/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes`

> **The resource download prints no progress** — only URL checks. It looks
> stuck but isn't. Verify with `du -sh /usr/local/hailo/resources` twice
> (should grow). Post-install is re-runnable and skips existing files:
> `source setup_env.sh && hailo-post-install`

---

## 3. Verify the stack

```bash
cd ~/hailo-apps
source setup_env.sh          # activates venv_hailo_apps

hailortcli scan              # should show the Hailo-8L device
hailo-post-install --help    # resources check (installs if needed)

# Interactive sanity check — shows a window with live detections:
hailo-detect --input /dev/video0
# (Ctrl-C to stop; arch is auto-detected from /usr/local/hailo/resources/.env)
```

---

## 4. Install this project into venv_hailo_apps

```bash
cd ~/HailoRover              # this repo's checkout on the Pi
git checkout feature/hailo-inference-layer

# Activate the Hailo venv without leaving the repo (wrapper for ~/hailo-apps/venv_hailo_apps)
source setup_env.sh

# Server deps (note: opencv-python gets replaced by opencv-python-headless — expected)
pip install -r raspi/server/requirements.txt

# hailoRT wheel deps that may be missing from the venv (harmless if already present)
pip install contextlib2 future

# The Option B inference layer (editable)
pip install -e raspi/hailo-layer
```

> **numpy constraint**: HailoRT 4.23 requires `numpy<2` — the server's
> `requirements.txt` pins `numpy>=1.26,<2` for exactly this reason. Do not
> `pip install -U numpy` in this venv.

---

## 5. Run with the Hailo engine

```bash
cd ~/HailoRover/raspi/server

# Create .env from the example:
cp .env.example .env
# edit: INFERENCE_ENGINE=hailo  (HEF_PATH=yolov8m is the default)

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Startup log should show `Inference engine: Hailo NPU (GStreamer pipeline takeover)`.
Open `http://<pi-ip>:8000` in a browser.

### Standalone smoke test (no server)

```bash
hailo-smoke --hef-path yolov8m --input /dev/video0 --width 640 --height 480 --run-time 30
# Expected: "SMOKE OK: N frames in 30s (... fps), M detections total"
```

---

## 6. Upgrading hailo-apps

1. `cd ~/hailo-apps && git fetch --tags && git checkout <new-tag> && pip install -e .`
   (check tags first — some have a `v` prefix, some don't)
2. Bump `HAILO_APPS_MIN_VERSION` / `HAILO_APPS_MAX_VERSION` in
   `raspi/hailo-layer/src/hailo_layer/pipeline/hailo_compat.py`
3. Review that one file against the release notes — **all** hailo-apps imports
   in this project flow through `hailo_compat.py`
4. `hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30`

---

## 7. Troubleshooting

### Hailo device not found
- Check PCIe connection — reseat the AI Hat
- Verify `/boot/firmware/config.txt` has `dtparam=pciex1_gen=3`
- Run `sudo dmesg | grep -i hailo` for kernel messages

### Resource download stalled
- Check growth: `du -sh /usr/local/hailo/resources` twice
- Ctrl+C and re-run `hailo-post-install` (resumes/skips existing files)

### `TAPPAS_POST_PROC_DIR environment variable not set`
- The app self-loads `/usr/local/hailo/resources/.env`; if it's missing, re-run
  `source setup_env.sh && hailo-post-install` from the hailo-apps clone

### Server logs "Hailo pipeline produced no frames"
- Camera busy/unplugged, or the HEF missing — check the hailo-apps logs and
  that `/usr/local/hailo/resources/models/hailo8l/yolov8m.hef` exists

### Low inference FPS
- Confirm PCIe Gen 3 is active: `sudo lspci -vv | grep -i "Speed"`
- Check power supply — RPi 5 + AI Hat can draw significant current
- Monitor temperature: `hailortcli fw-control read-temperature`
