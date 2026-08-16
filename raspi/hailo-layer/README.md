# hailo-layer

Hailo GStreamer inference layer (pipeline-takeover mode) for the HailoRover
detection server. A separate package (Option B) built on top of
[hailo-apps](https://github.com/hailo-ai/hailo-apps) — see the project
`PLAN.md` for the architecture decision.

## Layering

- `hailo_layer.types` / `hailo_layer.domain` — pure Python (no hailo/GStreamer
  imports), unit-testable on Windows:
  ```bash
  pip install -e "raspi/hailo-layer[dev]"
  pytest raspi/hailo-layer/tests
  ```
- `hailo_layer.pipeline` — hailo/GStreamer-aware; import only on the Pi inside
  `venv_hailo_apps` (requires the resources `.env` at
  `/usr/local/hailo/resources/.env`).

## Version pairing

| hailo-layer | hailo-apps | HailoRT | TAPPAS | OS |
|---|---|---|---|---|
| 0.1.x | 26.03.x | 4.23 | 5.1 | Raspberry Pi OS Trixie (Python 3.13) |

`hailo_layer.pipeline.runner` enforces the hailo-apps range at runtime
(`>=26.03.0,<26.04`).

## Quick start (on the Pi)

```bash
source ~/hailo-apps/setup_env.sh            # activates venv_hailo_apps
pip install -e raspi/hailo-layer
hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30
```

See `raspi/docs/hailo-setup.md` for the full setup.
