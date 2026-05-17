"""
UDP Receiver for BBB EMG Data
- Listens on UDP port 5005 for ESP32 monitoring data
- Logs to file and forwards to web dashboard via REST API
"""

import socket
import json
import threading
import time
from datetime import datetime
import requests
from pathlib import Path


class UDPReceiver:
    """
    UDP receiver for ESP32 monitoring data
    Logs incoming EMG data and relays to dashboard server
    """

    def __init__(self, port=5005, dashboard_url="http://localhost:8000/api/emg_data"):
        """
        Initialize UDP receiver

        Args:
            port: UDP port to listen on (default 5005)
            dashboard_url: FastAPI dashboard endpoint for EMG data
        """
        self.port = port
        self.dashboard_url = dashboard_url
        self.sock = None
        self.running = False
        self.thread = None
        self.data_count = 0

        # Create logs directory if not exists
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"emg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def start(self):
        """Start listening for UDP packets"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("0.0.0.0", self.port))
            self.running = True

            print(f"[UDP] Listening on port {self.port}...")
            print(f"[UDP] Log file: {self.log_file}")
            print(f"[UDP] Dashboard URL: {self.dashboard_url}")

            # Start receiver thread
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()

        except Exception as e:
            print(f"[Error] Failed to start UDP receiver: {e}")
            self.running = False

    def stop(self):
        """Stop listening"""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.thread:
            self.thread.join(timeout=2)
        print(f"[UDP] Stopped (received {self.data_count} packets)")

    def _listen_loop(self):
        """Main listening loop"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(512)
                self.data_count += 1

                # Parse JSON packet
                try:
                    packet = json.loads(data.decode("utf-8"))
                    self._process_packet(packet, addr)
                except json.JSONDecodeError as e:
                    print(f"[Error] Invalid JSON from {addr}: {e}")

            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    print(f"[Error] Receive error: {e}")

    def _process_packet(self, packet, addr):
        """
        Process received EMG data packet

        Args:
            packet: Parsed JSON data from ESP32
            addr: Source address tuple (IP, port)
        """
        timestamp = datetime.now().isoformat()

        # Log to file
        log_entry = {
            "timestamp": timestamp,
            "source": f"{addr[0]}:{addr[1]}",
            "data": packet,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Print summary
        if "level" in packet and "signal_pct" in packet:
            level_emoji = {
                "normal": "🟢",
                "warning": "🟡",
                "critical": "🔴",
            }.get(packet["level"], "❓")

            print(
                f"[{self.data_count:5d}] {level_emoji} Level={packet['level']:8s} | "
                f"RMS={packet['rms']:7.1f} | Signal={packet['signal_pct']:5.1f}%"
            )

        # Forward to dashboard
        try:
            response = requests.post(
                self.dashboard_url,
                json=log_entry,
                timeout=1,
            )
            if response.status_code != 200:
                print(f"[Dashboard] HTTP {response.status_code}: {response.text[:50]}")
        except requests.exceptions.RequestException as e:
            # Silently ignore dashboard connection errors (may not be running)
            pass

    def wait_until_stop(self):
        """Block until receiver is stopped"""
        if self.thread:
            self.thread.join()


def main():
    """Run UDP receiver"""
    receiver = UDPReceiver(port=5005, dashboard_url="http://localhost:8000/api/emg_data")
    receiver.start()

    try:
        print("\n[Info] Press Ctrl+C to stop\n")
        while receiver.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Stop] Received interrupt signal")
    finally:
        receiver.stop()


if __name__ == "__main__":
    main()
