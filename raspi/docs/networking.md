# Networking — LAN & Hotspot Configuration

## LAN Mode (Default)

The Raspberry Pi connects to your home router. Access the web UI from any device on the same network.

```bash
# Find the RPi's IP address
hostname -I

# Access from browser
http://<rpi-ip>:8000
```

No additional configuration needed — works out of the box.

---

## Hotspot Mode

The RPi creates its own WiFi network. Devices connect directly to the RPi without a router. Ideal for field use with the vehicle.

### Setup

```bash
# Install access point packages
sudo apt-get install -y hostapd dnsmasq

# Stop services until configured
sudo systemctl stop hostapd dnsmasq
```

#### 1. Configure static IP for wlan0

```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

#### 2. Configure DHCP server (dnsmasq)

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.50,255.255.255.0,24h
domain=vehicle.local
address=/vehicle.local/192.168.4.1
```

#### 3. Configure access point (hostapd)

```bash
sudo nano /etc/hostapd/hostapd.conf
```

```
interface=wlan0
driver=nl80211
ssid=ObjectDetect-Vehicle
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=vehicle2024
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

#### 4. Enable and start

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd dnsmasq
sudo systemctl start hostapd dnsmasq
```

#### 5. Toggle between modes

Set in `.env`:
```bash
# LAN mode
NETWORK_MODE=lan

# Hotspot mode
NETWORK_MODE=hotspot
```

When `NETWORK_MODE=hotspot`, the server startup script can:
- Stop `wpa_supplicant` (disconnect from router)
- Start `hostapd` + `dnsmasq`
- Serve at `192.168.4.1:8000`

---

## Access Reference

| Mode | URL | Network |
|---|---|---|
| LAN | `http://<rpi-ip>:8000` | Your home WiFi |
| Hotspot | `http://192.168.4.1:8000` | Connect to "ObjectDetect-Vehicle" WiFi first |
