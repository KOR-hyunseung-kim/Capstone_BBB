# WiFi Setup & Standalone Operation Guide

BBB can operate autonomously without a connected laptop by transmitting EMG monitoring data to a PC via WiFi UDP.

## Hardware Requirements

- BBB device (ESP32-S3) with WiFi capability
- PC or laptop with WiFi connectivity
- Both devices on the same WiFi network
- USB-C cable for initial flashing (not needed during operation)

## Step 1: Configure WiFi Credentials

Edit `firmware/config.py` with your WiFi network details:

```python
# WiFi Configuration
WIFI_ENABLED = True  # Enable WiFi UDP communication

# WiFi Network Settings
WIFI_SSID = "your_wifi_ssid"      # Change to your WiFi network name
WIFI_PASSWORD = "your_wifi_password"  # Change to your WiFi password

# PC Receiver Settings (where UDP data is sent)
PC_IP = "192.168.1.100"  # Change to your PC IP address
PC_PORT = 5005           # UDP port (match with receiver script)
```

### Finding Your PC IP Address

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter (typically `192.168.x.x` or `10.0.x.x`)

**Mac/Linux:**
```bash
ifconfig
```
Look for `inet` address under your WiFi interface

### Example Configuration
```python
WIFI_SSID = "MyHome-WiFi"
WIFI_PASSWORD = "SecurePassword123"
PC_IP = "192.168.1.50"
PC_PORT = 5005
```

## Step 2: Flash ESP32 with Configured Code

1. Connect ESP32-S3 to PC via USB-C cable
2. Open Thonny IDE
3. Select your device in **Tools → Options → Interpreter**
4. Upload the firmware files:
   - `firmware/config.py`
   - `firmware/boot.py`
   - `firmware/main.py`
   - `firmware/sensor/emg.py`
   - `firmware/ui/motor.py`, `led.py`, `oled.py`
   - `firmware/algo/emg_processor.py`
   - `firmware/comm/wifi.py`

5. Restart the device or press the **RESET** button

## Step 3: Run PC Receiver & Dashboard

On your PC:

### Option A: Using Dashboard Server (Recommended)

The dashboard provides real-time visualization of EMG data.

1. **Start the dashboard server:**
```bash
cd C:\4_1\BBB
python -m pip install -r requirements.txt  # If not already installed
python tools/dashboard/server.py
```

2. **Open web browser:**
   - Go to: `http://localhost:8000`
   - You should see the BBB monitoring dashboard

3. **The server automatically listens for UDP data** on port 5005

### Option B: Using Standalone UDP Receiver

If you don't want to run the full dashboard:

```bash
python tools/udp_receiver.py
```

This will:
- Listen for UDP packets on port 5005
- Log all EMG data to `tools/logs/emg_data_*.log`
- Print real-time monitoring data to console

## Step 4: Start BBB Device

With ESP32 powered (battery or USB):

1. Device will boot and start WiFi connection (5-10 seconds)
2. Once connected, it enters Safety Mode
3. Calibration message appears on OLED display (if enabled)
4. **Relax your arm** during 60-second calibration
5. After calibration, monitoring begins
6. EMG data transmits to PC every monitoring cycle (~100ms)

### Boot Sequence Expected Output
```
[Boot] Starting BBB firmware...
[Init] Initializing hardware...
[Init] EMG sensor... OK
[Init] Vibration motor... OK
[Init] RGB LED... OK
[Init] OLED display... OK
[Init] WiFi... OK
WiFi connected: 192.168.1.50

[Calib] Entering calibration in 3 seconds...
[Calib] Starting 60s calibration...
[Monitor] Calibration complete. Starting monitoring...
```

## Step 5: Monitor on Web Dashboard

The dashboard shows in real-time:
- **Fatigue Percentage** (0-100%)
- **Signal Level** (with color indicator)
  - 🟢 Green: Normal (≥90% signal)
  - 🟡 Yellow: Warning (70-90% signal)
  - 🔴 Red: Critical (<70% signal)
- **Median Frequency** (Hz) - if using raw EMG transmission
- **Real-time EMG waveform** graph

### Dashboard Features
- **Live Graph:** EMG signal waveform updates in real-time
- **Status Indicator:** Current fatigue level with color coding
- **Connection Status:** Shows when ESP32 is transmitting data
- **Historical Data:** Stores all monitoring data in logs

## Troubleshooting

### "WiFi connection failed" message

**Problem:** ESP32 can't connect to WiFi network

**Solutions:**
1. Check WiFi credentials in `config.py` are correct
2. Verify ESP32 is in range of WiFi router
3. Check router is not blocking ESP32 MAC address
4. Restart WiFi router
5. Try 2.4GHz WiFi (ESP32-S3 doesn't support 5GHz)

### Dashboard shows "No data received"

**Problem:** PC not receiving EMG data from ESP32

**Solutions:**
1. Verify `PC_IP` in `config.py` matches your actual PC IP
2. Check firewall isn't blocking UDP port 5005
3. Ensure ESP32 and PC are on same WiFi network
4. Verify ESP32 shows "WiFi connected" in debug output
5. Check dashboard server is running on port 8000

**Windows Firewall (if blocking):**
- Go to: **Settings → Privacy & Security → Windows Defender Firewall → Allow an app**
- Allow Python UDP communication on private networks

### EMG data corrupted or gaps in data

**Problem:** Received data has transmission errors or missing packets

**This is normal for UDP** - UDP doesn't guarantee delivery. For critical applications:
- Use the dashboard with raw EMG transmission (includes error detection)
- Or modify to use TCP instead of UDP (slower but guaranteed delivery)

## Performance Notes

### Data Rate
- **Monitoring Data Mode:** ~200 bytes per transmission × 10 Hz = 2 KB/s (very low bandwidth)
- **Raw EMG Mode:** ~400 bytes × 10 Hz = 4 KB/s
- Both modes use minimal WiFi bandwidth

### Latency
- **Monitoring Data:** 100-200ms (real-time visualization acceptable)
- **Raw EMG:** Same, plus dashboard processing

### Power Consumption
- WiFi enabled adds ~50mA while transmitting
- With 300mAh battery: ~6 hours continuous operation
- Can extend with sleep modes (future optimization)

## Advanced Configuration

### Custom Calibration Duration

Edit `firmware/config.py`:
```python
CALIBRATION_DURATION_SEC = 30  # Shorter: 30 seconds
CALIBRATION_DURATION_SEC = 120  # Longer: 2 minutes
```

### Debug Mode

To see detailed WiFi transmission logs:
```python
DEBUG = True
```

ESP32 will print WiFi connection info and any transmission errors

### Disable WiFi (Test Locally)

For testing without WiFi:
```python
WIFI_ENABLED = False
```

Device will operate autonomously with local LED/motor/OLED feedback only

## Security Notes

⚠️ **Important:**
- WiFi credentials are stored in plaintext in `config.py`
- Use this only on trusted home networks
- For production/public use, implement credential encryption
- Don't commit `config.py` with real WiFi passwords to version control

## Next Steps

1. Test WiFi connection in controlled environment
2. Calibrate with your arm in resting state
3. Monitor fatigue levels during physical activity
4. Adjust threshold values if needed (in `config.py`)
5. Log data for analysis using `tools/udp_receiver.py`

## See Also

- [Setup Guide](SETUP_ESP32.md) - Initial ESP32 flashing and setup
- [Debug Guide](DEBUG_GUIDE.md) - Local testing without WiFi
- [Hardware Documentation](02_HW/README.md) - Pin mappings and connections
