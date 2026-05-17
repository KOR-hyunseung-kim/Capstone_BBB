
"""
BBB Auto-boot Script
- Runs on ESP32 power-up
- Automatically starts Safety Mode
"""

import time

print("\n[Boot] Starting BBB firmware...")
time.sleep(1)

try:
    # Import and run main program
    import main
except Exception as e:
    print(f"[Error] Failed to start main: {e}")
