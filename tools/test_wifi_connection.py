"""
WiFi Connection Test Script
Verifies UDP receiver is working and can receive monitoring data
"""

import socket
import json
import sys
from datetime import datetime


def test_udp_receiver(port=5005, timeout=30):
    """
    Test UDP receiver by listening for incoming packets

    Args:
        port: UDP port to listen on (default 5005)
        timeout: How long to wait for data (seconds)

    Returns:
        True if data received, False if timeout
    """
    print(f"[Test] Setting up UDP receiver on port {port}...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.settimeout(timeout)

        print(f"[Test] Listening for ESP32 data for {timeout} seconds...")
        print("[Test] Make sure:")
        print("  1. ESP32 is powered on and connected to WiFi")
        print("  2. Firmware config.py has correct PC_IP and PC_PORT")
        print("  3. Calibration is complete (60 seconds)")
        print()

        received_count = 0
        start_time = datetime.now()

        while True:
            try:
                data, addr = sock.recvfrom(512)
                received_count += 1
                elapsed = (datetime.now() - start_time).total_seconds()

                try:
                    packet = json.loads(data.decode("utf-8"))
                    print(f"\n[✓] Received packet #{received_count} from {addr[0]}:{addr[1]}")
                    print(f"    RMS:        {packet.get('rms', 'N/A')}")
                    print(f"    Signal:     {packet.get('signal_pct', 'N/A'):.1f}%")
                    print(f"    Level:      {packet.get('level', 'N/A').upper()}")
                    print(f"    Iteration:  {packet.get('iteration', 'N/A')}")
                    print(f"    Elapsed:    {elapsed:.1f}s")

                    return True

                except json.JSONDecodeError as e:
                    print(f"\n[Error] Received data but invalid JSON: {e}")
                    print(f"        Raw data: {data[:100]}")

            except socket.timeout:
                sock.close()
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n[✗] No data received after {elapsed:.0f} seconds")
                print()
                print("Troubleshooting:")
                print("  1. Check PC_IP in firmware/config.py matches this PC")
                print("       Run: ipconfig (Windows) or ifconfig (Mac)")
                print("  2. Check WiFi network connectivity")
                print("  3. Verify port 5005 is not blocked by firewall")
                print("  4. Check ESP32 console for WiFi connection status")
                print("  5. Ensure calibration completed successfully")
                return False

    except Exception as e:
        print(f"\n[Error] Socket error: {e}")
        print("  Possible causes:")
        print("    - Port 5005 already in use")
        print("    - Insufficient permissions")
        print("    - Network interface error")
        return False


def test_firewall_settings():
    """Print instructions for firewall configuration"""
    print("\nFirewall Settings:")
    print("  Windows Firewall:")
    print("    1. Settings → Privacy & Security → Windows Defender Firewall")
    print("    2. Click 'Allow an app through firewall'")
    print("    3. Find Python and allow on Private networks")
    print()
    print("  Mac Firewall:")
    print("    1. System Settings → Security & Privacy → Firewall Options")
    print("    2. Add Python to allowed applications")
    print()
    print("  Linux (if using ufw):")
    print("    sudo ufw allow 5005/udp")
    print()


def main():
    """Run WiFi connection test"""
    print("=" * 60)
    print("BBB WiFi Connection Test")
    print("=" * 60)
    print()

    # Check if dashboard server is running
    print("[Check] Verifying PC network configuration...")
    try:
        import socket as sock_module
        hostname = sock_module.gethostname()
        ip_addr = sock_module.gethostbyname(hostname)
        print(f"  ✓ PC Hostname: {hostname}")
        print(f"  ✓ Local IP:    {ip_addr}")
        print()
    except Exception as e:
        print(f"  ✗ Could not determine IP: {e}")

    # Main test
    print("[Test] Starting UDP receiver test...")
    print()

    success = test_udp_receiver(port=5005, timeout=30)

    if success:
        print("\n" + "=" * 60)
        print("[Success] WiFi communication is working! ✓")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Start the dashboard: python tools/dashboard/server.py")
        print("  2. Open browser: http://localhost:8000")
        print("  3. View real-time monitoring data")
        return 0
    else:
        print("\n" + "=" * 60)
        print("[Failed] WiFi communication test failed ✗")
        print("=" * 60)
        test_firewall_settings()
        return 1


if __name__ == "__main__":
    sys.exit(main())
