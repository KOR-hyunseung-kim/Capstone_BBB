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
        self.send_count = 0
        self.last_reconnect_attempt = 0
        self.connect()
        self._create_socket()

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

    def _create_socket(self):
        """Create and configure UDP socket (reusable)"""
        try:
            if self.sock:
                self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Set non-blocking mode to avoid hanging
            self.sock.setblocking(False)
            if config.DEBUG:
                print(f"[WiFi] Socket created for {self.pc_address}")
        except Exception as e:
            if config.DEBUG:
                print(f"[WiFi] Socket creation error: {e}")
            self.sock = None

    def _check_connection(self):
        """Check if WiFi is still connected and reconnect if needed"""
        try:
            import network
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                print(f"[WiFi] ⚠️  Connection lost! Attempting to reconnect...")
                self.connected = False
                self.connect()
                if self.connected:
                    self._create_socket()
                    print(f"[WiFi] ✅ Reconnected!")
                    return True
                return False
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"[WiFi] Connection check error: {e}")
            return False

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
        if not self.connected or not self.sock:
            return

        # Periodically check connection (every 100 sends)
        if self.send_count % 100 == 0:
            if not self._check_connection():
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
            self.sock.sendto(data, self.pc_address)
            self.send_count += 1

        except OSError as e:
            # Memory error or socket issue - try to recreate socket
            if e.errno == 12:  # ENOMEM
                self._create_socket()
            elif e.errno == 107 or e.errno == 104:  # Transport endpoint / Connection reset
                print(f"[WiFi] Connection error, checking WiFi...")
                self._check_connection()
            if config.DEBUG and config.DEBUG_CONTROL_MODE:
                print(f"[WiFi] Send error: {e}")
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
        if not self.connected or not self.sock:
            return

        # Periodically check connection (every 100 sends)
        if self.send_count % 100 == 0:
            if not self._check_connection():
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
            self.sock.sendto(data, self.pc_address)
            self.send_count += 1

        except OSError as e:
            # Memory error or socket issue - try to recreate socket
            if e.errno == 12:  # ENOMEM
                self._create_socket()
            elif e.errno == 107 or e.errno == 104:  # Transport endpoint / Connection reset
                print(f"[WiFi] Connection error, checking WiFi...")
                self._check_connection()
            if config.DEBUG and config.DEBUG_SAFETY_MODE:
                print(f"[WiFi] Send error: {e}")
        except Exception as e:
            if config.DEBUG:
                print(f"[WiFi] Send error: {e}")

    def close(self):
        """Close WiFi connection"""
        if self.sock:
            self.sock.close()
