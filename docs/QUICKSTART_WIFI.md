# WiFi Operation Quick Start

Get BBB running with WiFi transmission in 5 minutes.

## Pre-flight Checklist

- [ ] ESP32-S3 flashed with latest firmware (from previous setup)
- [ ] WiFi network available (2.4GHz, WPA2/WPA3)
- [ ] PC and ESP32 on same network
- [ ] Dashboard dependencies installed: `pip install -r requirements.txt`

## 1. Configure WiFi (2 minutes)

Edit `firmware/config.py`:

```python
WIFI_ENABLED = True
WIFI_SSID = "YourNetworkName"        # Your WiFi SSID
WIFI_PASSWORD = "YourPassword"        # Your WiFi password
PC_IP = "192.168.1.YOUR_PC_IP"       # Find with: ipconfig (Windows) or ifconfig (Mac)
PC_PORT = 5005
```

Upload updated `config.py` to ESP32 using Thonny.

## 2. Start Dashboard Server (1 minute)

```bash
python tools/dashboard/server.py
```

Expected output:
```
[INFO] Application startup complete
[INFO] UDP receiver listening on port 5005
```

## 3. Power Up ESP32

Press **RESET** button or power cycle the device.

**Expected boot sequence:**
```
[WiFi] Listening on port 5005
WiFi connected: 192.168.1.100

[Calib] Starting 60s calibration...
[Monitor] Calibration complete. Starting monitoring...
```

## 4. Open Web Dashboard (1 minute)

Open browser and go to:
```
http://localhost:8000
```

You should see:
- Real-time fatigue percentage
- Color indicator (🟢 🟡 🔴)
- Live EMG waveform graph
- Status updates streaming

## 5. Test It!

Once calibrated, try:
1. **Relax arm** → Fatigue drops to 0%
2. **Flex bicep** → Fatigue increases toward 100%
3. **Hold contraction** → Maintains high fatigue level

Dashboard updates in real-time.

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| "WiFi connection failed" | Check SSID/password in config.py, restart device |
| Dashboard shows no data | Verify PC_IP matches `ipconfig`, check port 5005 not blocked |
| Data appears then stops | Check WiFi router distance, device may have dropped connection |

## Advanced: Local Testing (No WiFi)

If WiFi unavailable, run locally without dashboard:

```python
WIFI_ENABLED = False
DEBUG = True
```

Device will log everything to console when connected to PC serial port (Thonny).

## Next: Control Mode Setup

Once Safety Mode is working:
1. Implement IMU (MPU6050) sensor driver
2. Create cursor control algorithm
3. Test BLE HID mouse functionality
4. Integrate Control Mode into main.py

See `docs/CONTROL_MODE_SPEC.md` when available.

## See Full Documentation

- [WiFi Setup Guide](WIFI_SETUP.md) - Detailed configuration
- [Debug Guide](DEBUG_GUIDE.md) - Local debugging
- [Setup Guide](SETUP_ESP32.md) - Initial ESP32 flashing
