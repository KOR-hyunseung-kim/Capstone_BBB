# WiFi Troubleshooting Guide

Complete guide for resolving WiFi connectivity and data transmission issues.

## Quick Diagnostic

**Step 1: Run the test script**
```bash
python tools/test_wifi_connection.py
```

This will:
1. List your PC's IP address
2. Wait for ESP32 to send data
3. Report success or specific failure reason

## Issue: "WiFi connection failed"

### Symptom
ESP32 console shows:
```
[Init] WiFi... FAILED (connection)
```

### Diagnosis

**Check WiFi Credentials**
```python
# firmware/config.py
WIFI_SSID = "YourNetworkName"      # Must be EXACT case
WIFI_PASSWORD = "YourPassword"      # Must be EXACT
```

Common mistakes:
- SSID has space: `"My WiFi"` (spaces matter!)
- SSID is hidden (ESP32 may not find it)
- Password has special characters not escaped
- Mixing upper/lowercase

**Test Credentials**
1. Manually connect another device to same WiFi
2. If it works, credentials should work for ESP32

### Solutions

1. **Verify SSID Exactly**
   - Open WiFi settings on any device
   - Copy SSID exactly as shown
   - Update config.py with exact string

2. **Try 2.4GHz Only**
   - ESP32-S3 doesn't support 5GHz WiFi
   - Check router settings, may be broadcasting 5GHz only
   - Enable 2.4GHz if available

3. **Check WiFi Distance**
   - ESP32 range typically 20-50m
   - Try moving closer to router
   - Remove obstacles (walls, metal)

4. **Restart WiFi Router**
   - Turn off router for 30 seconds
   - Turn back on, wait 1-2 minutes for full boot
   - Then power ESP32

5. **Check MAC Address Filtering**
   - Some routers block unknown devices
   - Go to router settings (192.168.1.1 or 192.168.0.1)
   - Check for device MAC filtering enabled
   - Either disable or add ESP32 MAC address

### Debug WiFi Connection

Enable detailed WiFi debug output:

Edit `firmware/config.py`:
```python
DEBUG = True
```

Then check ESP32 console for:
- `[WiFi] Attempting connection to [SSID]...`
- `[WiFi] Connected: 192.168.x.x` ← Success!
- `[WiFi] Connection timeout` ← Failure reason

## Issue: "PC receives no data"

### Symptom
Dashboard shows empty graph, no packets arrive at PC

### Diagnosis

**Check PC IP Configuration**
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig
```

Look for your WiFi adapter's IPv4 address (typically starts with 192.168 or 10.0)

**Update firmware config.py**
```python
PC_IP = "192.168.1.YOUR_PC_IP"  # From ipconfig output
PC_PORT = 5005
```

**Verify ESP32 Sees PC IP**
Connect to Thonny and check console:
```
[WiFi] Sending to 192.168.1.100:5005
```

If shows wrong IP, update config.py and restart.

### Solutions

1. **Correct PC_IP Address**
   - Run `ipconfig` (Windows) or `ifconfig` (Mac)
   - Find WiFi adapter IP address (not 127.0.0.1!)
   - Update `firmware/config.py` PC_IP with exact value
   - Re-upload config.py to ESP32
   - Restart ESP32

2. **Check WiFi Router**
   - ESP32 and PC must be on SAME WiFi network
   - Check both are showing same SSID
   - Sometimes device connects to different band (2.4GHz vs 5GHz)

3. **Check Firewall**

   **Windows Firewall**:
   - Settings → Privacy & Security → Windows Defender Firewall
   - Click "Allow an app through firewall"
   - Find Python executable
   - Check "Private" checkbox is enabled
   - Click OK

   **Third-party Firewall** (Norton, McAfee, etc.):
   - Temporarily disable to test
   - If data arrives with firewall off, add exception for port 5005

   **Mac Firewall**:
   - System Settings → Security & Privacy → Firewall Options
   - Click "Firewall Options"
   - Find Python in list, ensure it's allowed
   - If not listed, add /usr/bin/python or similar

4. **Check Port 5005 is Available**
   ```bash
   # Windows: check if port is in use
   netstat -ano | findstr :5005
   
   # Mac/Linux:
   lsof -i :5005
   ```

   If port shows as ESTABLISHED or LISTENING by another program:
   - Use different port (e.g., 5006)
   - Update PC_PORT in config.py
   - Restart services

5. **Test Manually with netcat**
   ```bash
   # Windows (need to install netcat)
   nc -u -l -p 5005
   
   # Mac/Linux
   nc -u -l 5005
   ```

   This listens for any UDP on port 5005.
   If ESP32 sends data, you'll see it appear.

## Issue: "Inconsistent data" / "Gaps in graph"

### Symptom
Dashboard shows sporadic updates or missing data points

### Diagnosis

UDP packets may be dropped due to:
- WiFi interference (other networks, devices)
- Distance from router
- Network congestion
- WiFi dropout and recovery

This is **normal for UDP** - no guaranteed delivery.

### Solutions

1. **Reduce WiFi Interference**
   - Check for nearby WiFi networks on same channel
   - Use WiFi analyzer app to find best channel
   - Reconfigure router to less congested channel
   - Move router or ESP32 to better location

2. **Monitor Packet Loss**
   ```bash
   python tools/udp_receiver.py
   ```

   Check console output - if you see "Packet X, Packet Y" with gaps,
   UDP is dropping packets. This is expected behavior.

3. **Use WiFi with Better Signal**
   - Check signal strength: ESP32 should show -40 dBm or better
   - If weaker, move closer to router
   - Check for obstacles: walls, metal, microwaves

4. **Enable WiFi Error Recovery** (Future Enhancement)
   - Current code doesn't retry failed sends
   - Could add re-transmission logic
   - Or use TCP instead of UDP (guaranteed but slower)

## Issue: "Dashboard server won't start"

### Symptom
Running `python tools/dashboard/server.py` gives error

### Diagnosis

**Error: "Address already in use"**
```
[Errno 48] Address already in use
```

Another process is using port 8000.

**Solutions**:
1. Kill existing process:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID [PID] /F
   
   # Mac/Linux
   lsof -i :8000
   kill -9 [PID]
   ```

2. Use different port:
   ```bash
   # Edit tools/dashboard/server.py
   # Change: uvicorn.run(..., port=8000, ...)
   # To:     uvicorn.run(..., port=8001, ...)
   ```

**Error: "Module not found"**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**:
```bash
pip install -r requirements.txt
```

## Issue: "ESP32 boots then crashes"

### Symptom
Device shows boot messages then abruptly stops with exception

### Diagnosis

Could be:
- Memory allocation failure (1500+ samples in buffer)
- Module import error
- Hardware initialization error

### Solutions

1. **Enable Debug Output**
   ```python
   DEBUG = True
   DEBUG_EMG_VALUES = True
   ```

2. **Check Console for Exception**
   - Look for Python traceback
   - Note the exact error and line number
   - Check that file was uploaded correctly

3. **Disable Hardware Selectively**
   ```python
   ENABLE_EMG_SENSOR = True
   ENABLE_MOTOR = False     # Try disabling one at a time
   ENABLE_LED = False
   ENABLE_OLED = False
   WIFI_ENABLED = False
   ```

4. **Check Memory**
   - ESP32-S3 has 520KB RAM
   - WiFi + EMG takes ~100KB
   - Remaining ~420KB for buffers
   - Reduce EMG_CHUNK_SIZE if needed

## Issue: "Data format error" in dashboard

### Symptom
Dashboard terminal shows:
```
ERROR: Invalid JSON from ESP32
```

### Diagnosis

ESP32 is sending malformed JSON or corrupted packets.

### Solutions

1. **Check JSON Formatting**
   - Monitoring data should be:
     ```json
     {"rms": 450.5, "signal_pct": 85.2, "level": "warning", "iteration": 1}
     ```
   - Verify no extra commas, quotes
   - Check firmware/comm/wifi.py sends_monitoring_data() method

2. **Check Network Interference**
   - WiFi corruption could corrupt JSON
   - Try moving closer to router
   - Check for interference from other devices

3. **Enable UDP Logging**
   ```bash
   python tools/udp_receiver.py
   ```

   This logs raw packets to file, can inspect for corruption

## Issue: "WiFi was working, now it's not"

### Symptom
WiFi worked yesterday, now getting connection errors

### Diagnosis

Common causes:
- Router restarted (new IP address for ESP32)
- Router configuration changed
- Device moved to different network
- WiFi password changed

### Solutions

1. **Check if PC IP Changed**
   ```bash
   ipconfig
   ```

   If different from config.py, update and re-upload

2. **Restart Everything**
   - Restart WiFi router (30 seconds off)
   - Power cycle ESP32
   - Restart PC (if needed)

3. **Check WiFi Network**
   - Ensure ESP32 can see network
   - Try connecting with phone to verify network working
   - Check if SSID still matches config.py

4. **Update Time**
   - Some WiFi networks require correct time for connection
   - ESP32 may have lost system time
   - Need NTP sync (not yet implemented)

## Quick Reference Table

| Issue | Check | Fix |
|-------|-------|-----|
| No WiFi connection | SSID/password exact | Re-enter credentials |
| No data to PC | PC_IP matches ipconfig | Update config.py |
| Data gaps | Normal UDP behavior | Reduce interference |
| Firewall blocking | Windows Defender settings | Allow Python |
| Port in use | netstat/lsof output | Kill process or change port |
| Server crash | Debug output | Check console traceback |

## Still Not Working?

1. **Create Issue on GitHub**
   - Include exact error messages
   - Describe what you've tried
   - Attach console output/logs

2. **Check Documentation**
   - [WiFi Setup](WIFI_SETUP.md)
   - [Debug Guide](DEBUG_GUIDE.md)
   - [Verification Checklist](VERIFICATION_CHECKLIST.md)

3. **Contact Support**
   - Email: [project contact]
   - Include config.py settings (without passwords!)
   - Include console logs and error messages

---

**Last Updated**: 2026-05-06  
**Version**: 1.0
