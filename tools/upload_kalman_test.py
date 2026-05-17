#!/usr/bin/env python3
"""
Upload Kalman Filter test to ESP32-S3 via ampy
Usage: python tools/upload_kalman_test.py [--port COM5] [--run]
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def find_serial_ports():
    """Detect available serial ports."""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        return [(p.device, p.description) for p in ports]
    except ImportError:
        print("Please install pyserial: pip install pyserial")
        return []


def run_command(cmd, description=""):
    """Run shell command and report results."""
    if description:
        print(f"\n{description}...")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"[ERROR] {description} failed")
            if result.stderr:
                print(f"  stderr: {result.stderr}")
            return False

        if result.stdout:
            print(result.stdout)
        return True

    except subprocess.TimeoutExpired:
        print(f"[ERROR] {description} timed out")
        return False
    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return False


def check_ampy():
    """Check if ampy is installed."""
    cmd = "python -m pip show adafruit-ampy"
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def upload_and_test(port, run=True):
    """Upload test file and optionally run it."""

    firmware_dir = Path(__file__).parent.parent / "firmware"
    test_file = firmware_dir / "test_kalman_micropython.py"

    if not test_file.exists():
        print(f"[ERROR] Test file not found: {test_file}")
        return False

    print("=" * 60)
    print("KALMAN FILTER - ESP32-S3 UPLOAD TOOL")
    print("=" * 60)

    print(f"\nTest file: {test_file}")
    print(f"Serial port: {port}")

    if not check_ampy():
        print("\n[ERROR] ampy not installed")
        print("Install with: pip install adafruit-ampy")
        return False

    print("\n[1] Uploading test file to ESP32-S3...")

    cmd = (
        f'ampy --port {port} put "{test_file}" '
        "test_kalman_micropython.py"
    )

    if not run_command(cmd, "Upload"):
        print("\n[HINT] Board might be busy. Try:")
        print("  1. Disconnect USB, wait 2 seconds, reconnect")
        print("  2. Hold BOOT button while connecting")
        print("  3. Use Thonny IDE instead")
        return False

    print("[OK] File uploaded successfully")

    if run:
        print("\n[2] Running test on ESP32-S3...")

        cmd = f"ampy --port {port} run test_kalman_micropython.py"

        if run_command(cmd, "Execute test"):
            print("\n" + "=" * 60)
            print("[SUCCESS] Test completed!")
            print("=" * 60)
            return True
        else:
            print("\n[HINT] To run manually, use:")
            print("  import test_kalman_micropython")
            print("  test_kalman_micropython.run_all_tests()")
            return False
    else:
        print("\n[INFO] Upload complete. To run on board:")
        print("  import test_kalman_micropython")
        print("  test_kalman_micropython.run_all_tests()")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Upload Kalman Filter test to ESP32-S3"
    )
    parser.add_argument(
        "--port",
        "-p",
        default=None,
        help="Serial port (e.g., COM5, /dev/ttyUSB0)",
    )
    parser.add_argument(
        "--run",
        "-r",
        action="store_true",
        default=True,
        help="Run test after upload (default: True)",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Skip running test after upload",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available serial ports",
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable serial ports:")
        ports = find_serial_ports()
        if ports:
            for device, description in ports:
                print(f"  {device}: {description}")
        else:
            print("  No ports found")
        return 0

    port = args.port

    if not port:
        ports = find_serial_ports()
        if not ports:
            print("[ERROR] No serial ports detected")
            print("Try:")
            print("  1. Check USB cable connection")
            print("  2. Install CH340 driver")
            print("  3. List ports: python tools/upload_kalman_test.py --list")
            return 1

        if len(ports) == 1:
            port = ports[0][0]
            print(f"[Auto-detected] Using port: {port}")
        else:
            print("[ERROR] Multiple ports detected. Specify one:")
            for device, description in ports:
                print(f"  {device}: {description}")
            return 1

    run = not args.no_run
    success = upload_and_test(port, run=run)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
