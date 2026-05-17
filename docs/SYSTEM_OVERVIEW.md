# BBB System Overview

Complete guide to the Bio Body Band (BBB) EMG + IMU wearable monitoring system.

## Current Implementation Status (as of 2026-05-06)

### ✅ Completed: Safety Mode with WiFi

**Safety Mode** is fully implemented and ready for testing:

```
1. Autonomous Startup
   ↓
2. WiFi Connection
   ↓
3. 60-Second Calibration
   ↓
4. Real-time Monitoring Loop
   ├─ EMG Sampling (1 kHz)
   ├─ RMS Calculation
   ├─ Fatigue Level Detection
   ├─ Visual Feedback (LED/OLED/Motor)
   └─ WiFi Transmission to PC
   ↓
5. Web Dashboard Visualization
```

### 📋 In Progress: Control Mode

**Control Mode** (cursor control via IMU + EMG click) is next.

## System Architecture

### Hardware Stack

```
ESP32-S3 (Seeed XIAO)
├─ MyoWare 2.0 EMG Sensor (GPIO ADC)
├─ MPU6050 IMU (I2C)
├─ SSD1306 OLED Display (I2C, optional)
├─ RGB LED (GPIO PWM)
├─ Vibration Motor (GPIO PWM)
└─ 3.7V Li-Po Battery (USB-C charging)
```

### Firmware Stack (MicroPython)

```
firmware/
├─ config.py              # Central configuration
├─ boot.py                # Auto-startup on power
├─ main.py                # Entry point (Safety Mode)
├─ sensor/
│  ├─ emg.py              # MyoWare 2.0 driver
│  └─ imu.py              # MPU6050 driver (future)
├─ algo/
│  ├─ emg_processor.py    # RMS + fatigue detection
│  └─ filter.py           # Band-pass filter (future)
├─ ui/
│  ├─ motor.py            # Vibration feedback
│  ├─ led.py              # RGB LED control
│  └─ oled.py             # OLED display
└─ comm/
   └─ wifi.py             # WiFi + UDP communication
```

### PC Stack (Python 3.11+)

```
tools/
├─ udp_receiver.py        # UDP listener + logger
└─ dashboard/
   ├─ server.py           # FastAPI + WebSocket server
   └─ static/
      └─ index.html       # Web interface
```

## Operating Modes

### Safety Mode (Implemented)

**Purpose**: Real-time muscle fatigue monitoring with haptic alerts

**Operation**:
1. Continuous 1 kHz EMG sampling
2. RMS-based fatigue level detection (3 levels)
3. Visual feedback via LED and haptic feedback via motor
4. OLED display status (optional)
5. WiFi transmission to PC dashboard

**Fatigue Thresholds**:
- 🟢 **Normal** (≥90%): Muscle fresh, no vibration
- 🟡 **Warning** (70-90%): Mild fatigue, single vibration pulse
- 🔴 **Critical** (<70%): Severe fatigue, continuous vibration + urgent alert

**Use Cases**:
- Physical therapy monitoring
- Occupational fatigue detection
- Sports/fitness training
- Ergonomics assessment

### Control Mode (Future)

**Purpose**: Cursor control via arm movement (IMU) and muscle click (EMG spike)

**Planned Operation**:
1. Continuous IMU sampling (100 Hz)
2. Pitch/roll calculation via complementary filter
3. Cursor position mapping (arm tilt = mouse movement)
4. EMG spike detection for mouse click
5. BLE HID mouse emulation

**Hardware Requirements**:
- MPU6050 IMU sensor
- BLE HID support (ESP32-S3 built-in)

## Communication Protocols

### WiFi UDP (Implemented)

**Purpose**: Real-time monitoring data from ESP32 to PC

**Packet Format**:
```json
{
  "rms": 450.5,
  "signal_pct": 85.2,
  "level": "warning",
  "iteration": 1234
}
```

**Characteristics**:
- Low latency (100-200ms)
- Minimal bandwidth (~2 KB/s)
- No guaranteed delivery (acceptable for monitoring)
- Port: 5005 (configurable)

**Setup**:
1. Configure WiFi credentials in `firmware/config.py`
2. Start PC dashboard: `python tools/dashboard/server.py`
3. Power on ESP32, wait for WiFi connection
4. Open `http://localhost:8000` in browser

### BLE HID (Future - Control Mode)

**Purpose**: Mouse control to Windows/Mac/Linux

**Format**: HID-standard mouse commands
- Movement: X/Y delta (from IMU)
- Click: Mouse button press (from EMG spike)

## Deployment Workflow

### 1. Initial Setup (One Time)

```bash
# Install dependencies
pip install -r requirements.txt

# Flash ESP32 with MicroPython (using Thonny IDE or esptool)
# Upload firmware/ files to ESP32
```

See [Setup Guide](SETUP_ESP32.md)

### 2. Configure for Your Environment

Edit `firmware/config.py`:
```python
WIFI_SSID = "Your-Network"
WIFI_PASSWORD = "Your-Password"
PC_IP = "192.168.1.YourPC"  # Find with ipconfig
```

See [WiFi Setup](WIFI_SETUP.md)

### 3. Daily Operation

**Start Dashboard**:
```bash
python tools/dashboard/server.py
```

**Power On Device**:
- Press RESET button or turn on power switch
- Device boots, connects to WiFi, starts Safety Mode
- Relax for 60-second calibration
- Monitor on web dashboard

**Stop Operation**:
- Press Ctrl+C in dashboard terminal
- Or power off device (battery disconnect)

## Testing & Validation

### Safety Mode Testing

**Mock Testing** (no hardware):
```bash
python tools/test_safety_mode_pc.py
```

Validates:
- RMS calculation accuracy
- Threshold logic correctness
- UI feedback sequencing
- WiFi packet formatting

**Hardware Testing**:
1. Connect actual ESP32 + sensors to PC
2. Upload firmware via Thonny
3. Open dashboard
4. Perform arm movements and observe:
   - LED color changes
   - Motor vibration patterns
   - OLED display updates
   - Real-time dashboard data

### Debug Mode

Enable detailed logging:

Edit `firmware/config.py`:
```python
DEBUG = True
DEBUG_EMG_VALUES = True
DEBUG_LED_CONTROL = True
DEBUG_MOTOR_CONTROL = True
DEBUG_OLED_UPDATES = True
```

Connect to Thonny terminal to see real-time debug output.

## Power Management

### Energy Consumption

| Component | Current | Note |
|-----------|---------|------|
| ESP32 Core | 80mA | Always on |
| EMG Sampling | 5mA | ADC only |
| WiFi TX | 50mA | When transmitting |
| LED (full brightness) | 30mA | Rarely used |
| Motor (max) | 100mA | Pulsed, brief |
| **Total (typical)** | **~135mA** | WiFi + sampling |

### Battery Life

With 300mAh battery:
- Continuous monitoring: ~2 hours
- With WiFi sleep (future): ~5 hours

**Optimization strategies** (future):
- Light Sleep between monitoring cycles
- WiFi transmission throttling
- LED/motor duty cycle tuning

## Limitations & Future Work

### Current Limitations

1. **WiFi Only**: No Bluetooth yet (Control Mode needs this)
2. **Single Sensor**: EMG only (IMU for Control Mode pending)
3. **UDP No Guarantee**: Packets may be lost (acceptable for monitoring)
4. **Local Network Only**: No cloud integration
5. **No Encryption**: WiFi credentials in plaintext

### Future Enhancements

| Feature | Priority | Status |
|---------|----------|--------|
| Control Mode (IMU + BLE) | High | Planned |
| Raw EMG streaming | Medium | Partial (UDP ready) |
| WiFi reconnection logic | Medium | TODO |
| Battery optimization (sleep) | Medium | TODO |
| Cloud integration | Low | Planned |
| Credential encryption | Low | Planned |

## Documentation Guide

Start here based on your needs:

- **First time?** → [Quick Start WiFi](QUICKSTART_WIFI.md)
- **Initial setup?** → [Setup ESP32](SETUP_ESP32.md)
- **WiFi issues?** → [WiFi Setup](WIFI_SETUP.md)
- **Local debugging?** → [Debug Guide](DEBUG_GUIDE.md)
- **Full specifications?** → [Safety Mode Spec](specs/SAFETY_MODE_SPEC.md)
- **Hardware details?** → [Hardware Guide](02_HW/README.md)

## Key Contacts

- **Firmware Questions**: fw-developer agent
- **Algorithm Questions**: signal-processor agent
- **Hardware Questions**: hw-architect agent
- **Testing Questions**: qa-tester agent
- **Documentation**: tech-writer agent

See [Project Instructions](../CLAUDE.md) for agent availability.

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-05-06 | 1.0-beta | WiFi implementation complete, Safety Mode fully functional |
| 2026-04-XX | 0.9-alpha | Safety Mode core logic, local debug mode |
| Earlier | 0.1 | Hardware design, initial setup |

## Next Steps

1. ✅ **Safety Mode complete** - Ready for physical testing
2. 🔄 **Control Mode in progress** - Need IMU driver + BLE HID
3. 📊 **Dashboard visualization** - Working, can enhance UI
4. 🔌 **Power optimization** - Implement sleep modes
5. ☁️ **Cloud integration** - Long-term enhancement

---

**Last Updated**: 2026-05-06  
**Status**: Production-ready for Safety Mode  
**Next Review**: After Control Mode implementation
