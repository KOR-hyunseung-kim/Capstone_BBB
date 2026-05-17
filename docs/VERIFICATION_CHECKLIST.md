# WiFi Implementation Verification Checklist

Complete this checklist to verify WiFi functionality is working correctly.

## Code Review

- [x] `firmware/config.py` has WiFi configuration section
- [x] `firmware/comm/wifi.py` has no type hints (MicroPython compatible)
- [x] `firmware/main.py` imports WiFi modules conditionally
- [x] `firmware/main.py` calls `initialize_hardware()` with WiFi init
- [x] `firmware/boot.py` exists and auto-starts `main.py`
- [x] `tools/dashboard/server.py` parses monitoring data format
- [x] `tools/udp_receiver.py` created with logging capability
- [x] `requirements.txt` includes `requests` library

## Configuration Validation

Before testing, update these files:

**firmware/config.py**
- [ ] Set `WIFI_ENABLED = True`
- [ ] Set `WIFI_SSID = "your_network_name"`
- [ ] Set `WIFI_PASSWORD = "your_password"`
- [ ] Set `PC_IP = "192.168.x.x"` (verified with ipconfig)
- [ ] Set `PC_PORT = 5005`
- [ ] Calibration duration is reasonable (10-60 seconds)
- [ ] Debug mode preference set (DEBUG = True/False)

## Pre-Deployment Checks

### File Upload to ESP32

Using Thonny, verify all files are uploaded:
- [x] firmware/config.py
- [x] firmware/boot.py
- [x] firmware/main.py
- [x] firmware/sensor/emg.py
- [x] firmware/ui/motor.py
- [x] firmware/ui/led.py
- [x] firmware/ui/oled.py
- [x] firmware/algo/emg_processor.py
- [x] firmware/comm/wifi.py

Verify structure:
```
ESP32-S3 (/firmware/)
├─ config.py
├─ boot.py
├─ main.py
├─ sensor/
│  └─ emg.py
├─ ui/
│  ├─ motor.py
│  ├─ led.py
│  └─ oled.py
├─ algo/
│  └─ emg_processor.py
└─ comm/
   └─ wifi.py
```

### PC Environment

- [ ] Python 3.8+ installed
- [ ] Requirements installed: `pip install -r requirements.txt`
- [ ] UDP port 5005 not blocked by firewall
- [ ] PC can ping WiFi router
- [ ] PC is on same network as WiFi router

## Boot Sequence Verification

### Start Dashboard Server

```bash
cd C:\4_1\BBB
python tools/dashboard/server.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     UDP receiver listening on port 5005
INFO:     Background tasks started
```

✓ Server is ready

### Power On ESP32

1. [ ] Press RESET button on ESP32
2. [ ] Watch Thonny terminal output (if connected)
3. [ ] Look for these messages:

```
[Boot] Starting BBB firmware...
[Init] Initializing hardware...
[Init] EMG sensor... OK
[Init] Vibration motor... (OK/DISABLED)
[Init] RGB LED... (OK/DISABLED)
[Init] OLED display... (OK/DISABLED)
[Init] WiFi... OK
WiFi connected: 192.168.x.x
```

4. [ ] If WiFi connects, should see in dashboard terminal:
```
INFO: Received monitoring data from 192.168.x.x
```

5. [ ] Watch for calibration prompt:
```
[Calib] Entering calibration in 3 seconds...
        ⚠️  Please RELAX your arm (no muscle contraction)
[Calib] Starting 60s calibration...
```

6. [ ] Relax arm for full calibration period
7. [ ] After calibration:
```
[Monitor] Calibration complete. Starting monitoring...
```

✓ Boot sequence complete

## Dashboard Verification

### Web Interface

1. [ ] Open `http://localhost:8000` in web browser
2. [ ] Page loads without errors
3. [ ] Dashboard displays:
   - [ ] "BBB Safety Mode" title
   - [ ] Fatigue percentage display
   - [ ] Color indicator (currently color)
   - [ ] Status text (OK, WARNING, CRITICAL)
   - [ ] EMG graph (if raw samples received)

### Data Reception

1. [ ] Minimize arm movement for 10 seconds
2. [ ] Dashboard fatigue % should decrease (muscle relaxing)
3. [ ] LED color should become green (if connected)
4. [ ] Terminal shows:
```
Monitoring: NORMAL (XX.X%) RMS=...
```

## Functional Testing

### LED Feedback (if hardware present)

1. [ ] At startup: LED is green (normal state)
2. [ ] Relax arm: LED stays green (signal ~100%)
3. [ ] Flex arm lightly: LED turns yellow (signal 70-90%)
4. [ ] Flex arm hard: LED turns red (signal <70%)

### Motor Feedback (if hardware present)

1. [ ] At startup: Motor off (no vibration)
2. [ ] Signal drops to 70-89%: Motor vibrates once (warning)
3. [ ] Signal drops below 70%: Motor vibrates continuously (critical)
4. [ ] Return to normal: Motor stops

### OLED Display (if hardware present)

1. [ ] Shows "BBB Safety Mode" title
2. [ ] Shows current fatigue percentage
3. [ ] Shows fatigue bar graph
4. [ ] Shows status text (OK / WARNING / CRITICAL)
5. [ ] Updates every 100-200ms

## Data Logging

### Log File Verification

Look for logs in `tools/logs/`:

```bash
dir tools\logs\
```

Files should exist:
- [ ] `emg_data_20260506_HHMMSS.log`

Check log content:
```bash
type tools\logs\emg_data_*.log
```

Should show JSON entries:
```json
{"timestamp": "2026-05-06T14:30:45.123", "source": "192.168.x.x:5005", "data": {"rms": 450.5, "signal_pct": 85.2, "level": "warning", "iteration": 1234}}
```

- [ ] Log file has multiple entries (not just one)
- [ ] Entries increase in iteration number
- [ ] Timestamps are sequential
- [ ] Levels change (NORMAL → WARNING → CRITICAL based on activity)

## Troubleshooting Verification

If any checks fail, refer to troubleshooting:

### WiFi Connection Issues

```bash
# Check ESP32 console output for WiFi messages
# Should see: "WiFi connected: 192.168.x.x"
# If not, verify:
- WIFI_SSID matches exactly
- WIFI_PASSWORD is correct
- Router not blocking MAC address
- 2.4GHz WiFi (not 5GHz)
```

### No Data Received

```bash
# Check PC IP configuration
ipconfig  # Find "IPv4 Address" of your WiFi adapter

# Verify in config.py:
PC_IP = "192.168.x.x"  # Must match ipconfig output

# Check firewall
# Windows Firewall > Allow an app > Add Python
```

### Dashboard Not Loading

```bash
# Verify server is running
# Should see "Uvicorn running" message

# Check port 8000 is available
# Try different port if needed in server.py

# Try in browser:
http://127.0.0.1:8000
http://localhost:8000
```

## Performance Baseline

Record these baseline numbers for comparison:

| Metric | Expected | Actual |
|--------|----------|--------|
| Boot time | <10s | ___ |
| WiFi connect time | <5s | ___ |
| Calibration time | ~60s | ___ |
| Data transmission latency | <200ms | ___ |
| Dashboard update rate | ~10 Hz | ___ |
| Memory usage (ESP32) | <70% | ___ |

## Regression Testing

After any code changes, re-verify:

- [ ] All 9 firmware files upload without errors
- [ ] Boot sequence completes
- [ ] WiFi connects within 10 seconds
- [ ] Dashboard receives data within 30 seconds
- [ ] Fatigue levels respond to arm movement
- [ ] Log files have no duplicate entries
- [ ] Error rate < 1%

## Sign-Off

**Verification Date**: ___/___/______

**Verified By**: _________________

**Notes**: 
```
[Space for comments or issues found]
```

**Status**: [ ] PASS [ ] FAIL [ ] PARTIAL

If FAIL or PARTIAL, create issue in GitHub or document in history/

---

## Quick Verification (5 min)

If you don't have time for full checklist:

1. Start dashboard: `python tools/dashboard/server.py`
2. Power on ESP32
3. Check for "WiFi connected" message
4. Open `http://localhost:8000`
5. Verify graph updating
6. Flex arm, verify fatigue % changes

If all 5 steps pass, system is working! ✓
