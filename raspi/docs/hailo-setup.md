# Hailo AI Hat Setup Guide

Actual stack on the vehicle's Pi: Hailo AI HAT+ (Hailo-8L, 26 TOPS) on
Raspberry Pi 5 with **hailo-apps** (successor of the deprecated
`hailo-rpi5-examples`).

## Version pairing — do not drift

| Component | Version |
|---|---|
| hailo-apps | 26.3.x |
| HailoRT | 4.23.0 |
| TAPPAS (postprocess) | 5.1.0 |
| Raspberry Pi OS | Trixie (64-bit), Python 3.13 |
| hailo-layer (this repo) | 0.1.x — requires hailo-apps `>=26.3.0,<26.4.0` |

Mixing versions breaks confusingly — old infra tags with TAPPAS 5.1 fail the
C++ postprocess compile (`'class HailoTensor' has no member named 'vstream_info'`).

---

## 1. Enable PCIe Gen 3 (once)

```bash
sudo nano /boot/firmware/config.txt    # add: dtparam=pciex1_gen=3
sudo reboot
lspci | grep Hailo                     # device visible
```

---

## 2. One-shot setup

hailo-apps lives **inside this repo** (`hailo-apps/`, gitignored). Clone it
once, then run `setup.sh` for everything:

```bash
cd ~/Documents/Projects/HailoRover
git clone https://github.com/hailo-ai/hailo-apps.git
bash setup.sh
```

`setup.sh` runs, in order:

1. `sudo ./install.sh` — HailoRT + TAPPAS (apt), `venv_hailo_apps`, editable
   install, post-install (~1.5 GB models → `/usr/local/hailo/resources`,
   C++ postprocess `.so` → `/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes`)
2. Editable-install refresh — repairs absolute paths if the clone was moved
3. Server requirements (+ `contextlib2`, `future` for the hailoRT wheel)
4. `pip install -e raspi/hailo-layer`

Re-runnable; downloads and steps already done are skipped. The resource
download prints no progress — it looks stuck but isn't (`du -sh
/usr/local/hailo/resources` twice to confirm growth).

Activate the venv anytime, from anywhere in the repo (fast — detects an
existing install and skips straight to activation):

```bash
source setup.sh
```

---

## 3. Run

```bash
source setup.sh
hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30   # pipeline check

cd raspi/server
cp .env.example .env                        # set INFERENCE_ENGINE=hailo
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# → log: "Inference engine: Hailo NPU (GStreamer pipeline takeover)"
# → browser: http://<pi-ip>:8000 (build + deploy the frontend once: cd ../frontend && npm run deploy)
```

---

## 4. Upgrading hailo-apps

1. `cd hailo-apps && git fetch --tags && git checkout <new-tag>` (check tags
   first — some have a `v` prefix, some don't), then `bash ../setup.sh`
2. Bump `HAILO_APPS_MIN/MAX_VERSION` in
   `raspi/hailo-layer/src/hailo_layer/pipeline/hailo_compat.py`
3. Review that one file against the release notes — **all** hailo-apps imports
   flow through it
4. `hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30`

---

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `hailortcli scan` empty | reseat HAT; check `dtparam=pciex1_gen=3`; `sudo dmesg \| grep -i hailo` |
| Resource download "stuck" | it's silent — check `du` growth; Ctrl+C + re-run `bash setup.sh` |
| `TAPPAS_POST_PROC_DIR` missing | re-run `bash setup.sh` (app self-loads `/usr/local/hailo/resources/.env`) |
| Server: "Hailo pipeline produced no frames" | camera busy/unplugged, or HEF missing from `/usr/local/hailo/resources/models/hailo8/` |
| Low FPS | PCIe Gen 3 active? `sudo lspci -vv \| grep -i Speed`; check power supply |
| `numpy<2` conflict | never `pip install -U numpy` in the venv — pin is `>=1.26,<2` (HailoRT constraint) |
