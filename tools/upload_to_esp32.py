"""
자동 업로드 스크립트 for Thonny
모든 firmware 파일을 ESP32에 업로드
"""

import os
import shutil
from pathlib import Path


def upload_files():
    """Upload firmware files to Thonny's temporary directory"""

    # 경로 설정
    firmware_dir = Path(__file__).parent.parent / "firmware"

    if not firmware_dir.exists():
        print(f"Error: firmware directory not found at {firmware_dir}")
        return False

    print("=" * 70)
    print("BBB Firmware Upload Tool for Thonny")
    print("=" * 70)

    print(f"\nSource: {firmware_dir}")
    print("\nFiles to upload:")

    # 업로드할 파일 목록
    files_to_upload = [
        "config.py",
        "main.py",
        "sensor/emg.py",
        "algo/emg_processor.py",
        "ui/motor.py",
        "ui/led.py",
        "ui/oled.py",
        "comm/wifi.py",
    ]

    for file_path in files_to_upload:
        full_path = firmware_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  [OK] {file_path:40s} ({size:6d} bytes)")
        else:
            print(f"  [XX] {file_path:40s} (NOT FOUND)")

    print("\n" + "=" * 70)
    print("Upload Instructions for Thonny:")
    print("=" * 70)
    print("""
Step 1: Open Thonny and connect to ESP32-S3

Step 2: Split the view (View → Files + Shell)
  Left pane (Files):  C:\\4_1\\BBB\\firmware
  Right pane:         MicroPython device (/)

Step 3: Create folders in right pane
  Right-click / → New folder → "sensor"
  Right-click / → New folder → "algo"
  Right-click / → New folder → "ui"
  Right-click / → New folder → "comm"

Step 4: Upload files using drag & drop
  Drag .py files from left to corresponding folders on right

  Examples:
  - config.py from left → drag to / on right
  - sensor/emg.py from left → drag to /sensor on right
  - algo/emg_processor.py from left → drag to /algo on right
  - etc.

Step 5: Verify
  Right pane should show:
  /
  ├── config.py
  ├── main.py
  ├── sensor/
  │   └── emg.py
  ├── algo/
  │   └── emg_processor.py
  ├── ui/
  │   ├── motor.py
  │   ├── led.py
  │   └── oled.py
  └── comm/
      └── wifi.py

Step 6: Run
  Press F5 or Click "Run" button
  OR type in Shell: exec(open('main.py').read())
""")

    print("=" * 70)
    print("\nIMPORTANT NOTES:")
    print("- Do NOT upload __pycache__ folder")
    print("- Do NOT upload .pyc files")
    print("- Only upload .py files")
    print("- Folder structure is important (sensor/, algo/, ui/, comm/)")
    print("=" * 70)

    return True


if __name__ == "__main__":
    upload_files()
    input("\nPress Enter to close...")
