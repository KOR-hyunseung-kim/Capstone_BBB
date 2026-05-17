"""
WiFi UDP Communication Module
Sends sensor data to PC dashboard (Control Mode & Safety Mode)
"""

import socket
import json
import time
import config


class WiFiManager:
    """Manage WiFi connection and UDP data transmission"""

    def __init__(self):
        """Initialize WiFi manager"""
        self.sock = None
        self.connected = False
        self.pc_address = (config.PC_IP, config.PC_PORT)
        self.connect()

    def connect(self):
        """Connect to WiFi network"""
        if not config.WIFI_ENABLED:
            print("[WiFi] WiFi disabled in config")
            return

        try:
            import network
            import time as time_module

            # Connect to WiFi
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)

            if not wlan.isconnected():
                print(f"[WiFi] Connecting to {config.WIFI_SSID}...")
                wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

                # Wait for connection
                timeout = config.WIFI_CONNECT_TIMEOUT
                start_time = time_module.time()
                while not wlan.isconnected() and (time_module.time() - start_time) < timeout:
                    time_module.sleep(0.1)

            if wlan.isconnected():
                print(f"[WiFi] ✅ Connected! IP: {wlan.ifconfig()[0]}")
                self.connected = True
            else:
                print("[WiFi] ❌ Connection failed")

        except Exception as e:
            print(f"[WiFi] Connection error: {e}")

    def send_control_mode_data(self, pitch, roll, cursor_x, cursor_y, emg_raw, click_detected):
        """
        Send Control Mode data to PC dashboard

        Args:
            pitch: Arm pitch angle (degrees)
            roll: Arm roll angle (degrees)
            cursor_x: Cursor X position (0~1024)
            cursor_y: Cursor Y position (0~1024)
            emg_raw: Raw EMG value
            click_detected: Boolean, click detected
        """
        if not self.connected:
            return

        try:
            packet = {
                "mode": "control",
                "pitch": round(pitch, 1),
                "roll": round(roll, 1),
                "cursor_x": cursor_x,
                "cursor_y": cursor_y,
                "emg_raw": emg_raw,
                "click_detected": click_detected,
                "timestamp": time.time(),
            }

            data = json.dumps(packet).encode()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data, self.pc_address)
            sock.close()

        except Exception as e:
            if config.DEBUG:
                print(f"[WiFi] Send error: {e}")

    def send_safety_mode_data(self, rms, fatigue_pct, level, baseline_rms):
        """
        Send Safety Mode data to PC dashboard

        Args:
            rms: Current RMS value
            fatigue_pct: Fatigue percentage (0~100)
            level: Fatigue level ("normal", "warning", "critical")
            baseline_rms: Baseline RMS value
        """
        if not self.connected:
            return

        try:
            packet = {
                "mode": "safety",
                "rms": round(rms, 1),
                "signal_pct": round(fatigue_pct, 1),
                "level": level,
                "baseline_rms": round(baseline_rms, 1) if baseline_rms else 0,
                "timestamp": time.time(),
            }

            data = json.dumps(packet).encode()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data, self.pc_address)
            sock.close()

        except Exception as e:
            if config.DEBUG:
                print(f"[WiFi] Send error: {e}")

    def close(self):
        """Close WiFi connection"""
        if self.sock:
            self.sock.close()
