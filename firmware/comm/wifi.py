"""
WiFi UDP Communication for BBB
- Send: Raw EMG/IMU data to PC
- Receive: Fatigue analysis results from PC
"""

import socket
import json
import network
from typing import Dict, Optional, Tuple


class WiFiManager:
    """WiFi connection and status management"""

    def __init__(self, ssid: str, password: str):
        """
        Initialize WiFi manager

        Args:
            ssid: WiFi network name
            password: WiFi password
        """
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False

    def connect(self, timeout_sec: int = 10) -> bool:
        """
        Connect to WiFi network

        Args:
            timeout_sec: Connection timeout in seconds

        Returns:
            True if connected, False otherwise
        """
        if self.wlan.isconnected():
            return True

        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)

        for _ in range(timeout_sec * 10):
            if self.wlan.isconnected():
                self.connected = True
                ip_info = self.wlan.ifconfig()
                print(f"WiFi connected: {ip_info[0]}")
                return True
            import time

            time.sleep(0.1)

        print("WiFi connection failed")
        return False

    def disconnect(self) -> None:
        """Disconnect from WiFi"""
        self.wlan.disconnect()
        self.connected = False

    def get_ip(self) -> Optional[str]:
        """Get IP address"""
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None

    def is_connected(self) -> bool:
        """Check connection status"""
        return self.wlan.isconnected()


class UDPComm:
    """
    UDP communication for EMG data transmission and analysis result reception
    """

    def __init__(self, pc_ip: str, pc_port: int = 5005):
        """
        Initialize UDP communication

        Args:
            pc_ip: PC IP address
            pc_port: UDP port (default 5005)
        """
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.sock_tx = None
        self.sock_rx = None
        self.local_port = pc_port  # Use same port for bidirectional communication

    def init_transmitter(self) -> bool:
        """Initialize UDP socket for sending data"""
        try:
            self.sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return True
        except Exception as e:
            print(f"UDP TX init error: {e}")
            return False

    def init_receiver(self) -> bool:
        """Initialize UDP socket for receiving analysis results"""
        try:
            self.sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_rx.bind(("0.0.0.0", self.local_port))
            self.sock_rx.settimeout(0.1)  # Non-blocking with 100ms timeout
            return True
        except Exception as e:
            print(f"UDP RX init error: {e}")
            return False

    def send_emg_data(self, emg_samples: list) -> bool:
        """
        Send EMG data to PC

        Args:
            emg_samples: List of EMG ADC values

        Returns:
            True if sent successfully
        """
        if not self.sock_tx:
            return False

        try:
            payload = {"emg": emg_samples}
            data = json.dumps(payload).encode()
            self.sock_tx.sendto(data, (self.pc_ip, self.pc_port))
            return True
        except Exception as e:
            print(f"EMG send error: {e}")
            return False

    def send_imu_data(self, accel: Tuple, gyro: Tuple) -> bool:
        """
        Send IMU data to PC

        Args:
            accel: (x, y, z) acceleration
            gyro: (x, y, z) angular velocity

        Returns:
            True if sent successfully
        """
        if not self.sock_tx:
            return False

        try:
            payload = {
                "imu": {
                    "accel": list(accel),
                    "gyro": list(gyro),
                }
            }
            data = json.dumps(payload).encode()
            self.sock_tx.sendto(data, (self.pc_ip, self.pc_port))
            return True
        except Exception as e:
            print(f"IMU send error: {e}")
            return False

    def recv_analysis_result(self) -> Optional[Dict]:
        """
        Receive analysis results from PC (non-blocking)

        Returns:
            {
                "fatigue_pct": float,
                "mf": float,
                "level": str,
            }
            or None if no data available
        """
        if not self.sock_rx:
            return None

        try:
            data, _ = self.sock_rx.recvfrom(256)
            result = json.loads(data.decode())
            return result
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Analysis result recv error: {e}")
            return None

    def close(self) -> None:
        """Close UDP sockets"""
        if self.sock_tx:
            self.sock_tx.close()
        if self.sock_rx:
            self.sock_rx.close()
