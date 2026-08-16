# Hailo AI Hat Setup Guide

This guide walks through installing the HailoRT driver and Python SDK on Raspberry Pi 5 for the Hailo AI Hat (26 TOPS NPU).

## Prerequisites

- Raspberry Pi 5 (8 GB RAM recommended)
- Raspberry Pi OS (64-bit, Bookworm)
- Hailo AI Hat physically installed on the GPIO/PCIe header
- Internet connection for package downloads

---

## 1. Enable PCIe Gen 3

The Hailo AI Hat connects via PCIe. Edit the boot config:

```bash
sudo nano /boot/firmware/config.txt
```

Add at the end:
```
# Enable PCIe Gen 3 for Hailo AI Hat
dtparam=pciex1_gen=3
```

Reboot:
```bash
sudo reboot
```

Verify the Hailo device is visible:
```bash
lspci | grep Hailo
# Expected: Hailo Technologies Ltd. Device ...
```

---

## 2. Install HailoRT (Runtime Driver)

```bash
# Add Hailo repository
sudo apt-get update
sudo apt-get install -y hailo-all

# Or install individual components:
# sudo apt-get install -y hailort
# sudo apt-get install -y hailo-firmware
```

Verify installation:
```bash
hailortcli scan
# Should show: Hailo-8L device found
hailortcli fw-control identify
# Shows firmware version and device info
```

---

## 3. Install HailoRT Python API

```bash
# Activate your virtual environment first
source venv/bin/activate

# Install the Python bindings
pip install hailo-platform
```

Test from Python:
```python
import hailo_platform
devices = hailo_platform.Device.scan()
print(f"Found {len(devices)} Hailo device(s)")
```

---

## 4. Verify Performance

Run the built-in benchmark:
```bash
hailortcli benchmark --model-path models/yolov8s.hef
```

Expected: ~30 FPS on YOLOv8s with Hailo-8L.

---

## 5. Troubleshooting

### Hailo device not found
- Check PCIe connection — reseat the AI Hat
- Verify `/boot/firmware/config.txt` has `dtparam=pciex1_gen=3`
- Run `sudo dmesg | grep -i hailo` for kernel messages

### Low inference FPS
- Confirm PCIe Gen 3 is active: `sudo lspci -vv | grep -i "Speed"`
- Check power supply — the RPi 5 + AI Hat can draw significant current
- Monitor temperature: `hailortcli fw-control read-temperature`

### Python import error
- Ensure `hailo-platform` is installed in the correct venv
- The HailoRT Python API requires the C runtime (`libhailort.so`) to be installed first
