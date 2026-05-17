"""
BBB Main Firmware - Dual Mode Operation (Safety + Control)
Mode switching via GPIO21 button
"""

import time
from machine import Pin
import config

# Import mode modules
try:
    from safety_mode import safety_mode_loop
    from control_mode import control_mode_loop
    MODES_AVAILABLE = True
except ImportError as e:
    print(f"[Error] Mode import failed: {e}")
    MODES_AVAILABLE = False


def print_startup_banner():
    """Print startup information and configuration"""
    print("=" * 70)
    print("BBB (Bio Body Band) - Dual Mode Firmware")
    print("=" * 70)
    print("[INFO] Available Modes:")
    print("  1. Safety Mode   - EMG fatigue monitoring (LED + Motor feedback)")
    print("  2. Control Mode  - Arm tilt cursor control + EMG click detection")
    print("[INFO] Mode Switch: GPIO21 Button (tap to switch, hold to reset)")
    print("=" * 70)
    print("\n[CONFIG] Hardware Configuration:")
    print(f"  EMG Sensor:     {('ENABLED' if config.ENABLE_EMG_SENSOR else 'DISABLED')}")
    print(f"  IMU Sensor:     {('ENABLED' if config.ENABLE_IMU_SENSOR else 'DISABLED')}")
    print(f"  RGB LED:        {('ENABLED' if config.ENABLE_LED else 'DISABLED')}")
    print(f"  Vibrator Motor: {('ENABLED' if config.ENABLE_MOTOR else 'DISABLED')}")
    print(f"  OLED Display:   {('ENABLED' if config.ENABLE_OLED else 'DISABLED')}")
    print(f"\n[CONFIG] Debug Settings:")
    print(f"  Global DEBUG:     {('ON' if config.DEBUG else 'OFF')}")
    print(f"  Safety Mode:      {('VERBOSE' if config.DEBUG_SAFETY_MODE else 'NORMAL')}")
    print(f"  Control Mode:     {('VERBOSE' if config.DEBUG_CONTROL_MODE else 'NORMAL')}")
    print(f"  EMG Values:       {('PRINT' if config.DEBUG_EMG_VALUES else 'SILENT')}")
    print(f"  IMU Values:       {('PRINT' if config.DEBUG_IMU_VALUES else 'SILENT')}")
    print(f"  LED Control:      {('PRINT' if config.DEBUG_LED_CONTROL else 'SILENT')}")
    print(f"  Motor Control:    {('PRINT' if config.DEBUG_MOTOR_CONTROL else 'SILENT')}")
    print("=" * 70)
    print()


def get_default_mode():
    """
    Determine default startup mode
    Returns: "safety" or "control"
    """
    # Default to Safety Mode for safety reasons
    return "safety"


def mode_switch_handler(mode_switch_pin=21):
    """
    Detect mode switch button press

    Args:
        mode_switch_pin: GPIO pin for mode switch

    Returns:
        "tap" (short press), "hold" (long press), or None
    """
    switch = Pin(mode_switch_pin, Pin.IN, Pin.PULL_UP)

    # Debounce: wait for stable press
    if switch.value() == 0:  # Button pressed (LOW)
        time.sleep_ms(50)  # Debounce delay

        if switch.value() == 0:  # Still pressed after debounce
            press_start = time.ticks_ms()

            # Wait for release
            while switch.value() == 0:
                time.sleep_ms(10)

            press_duration = time.ticks_diff(time.ticks_ms(), press_start)

            if press_duration > 2000:
                return "hold"  # Hold > 2 seconds
            else:
                return "tap"  # Tap < 2 seconds

    return None


def print_mode_info(mode):
    """Print mode-specific startup information and configuration"""
    if mode == "safety":
        print("\n" + "=" * 70)
        print("SAFETY MODE - EMG Fatigue Monitoring")
        print("=" * 70)
        print("[Setup] Calibration: Keep arm RELAXED, no muscle contraction")
        if config.DEBUG_SAFETY_MODE:
            print("        Duration: %ds" % config.CALIBRATION_DURATION_SEC)
            print("        Normal threshold: >= %d%%" % config.EMG_NORMAL_THRESHOLD)
            print("        Warning threshold: %d~%d%%" % (config.EMG_WARNING_THRESHOLD, config.EMG_NORMAL_THRESHOLD))
        print("[Setup] Monitoring: Watch LED colors and feel motor feedback")
        print("        🟢 Green   = Normal (< 70% fatigue)")
        print("        🟡 Yellow  = Warning (70~90% fatigue)")
        print("        🔴 Red     = Critical (> 90% fatigue)")
        print("[Setup] Motor: Silent → Short pulses (warning) → Rapid pulses (critical)")
        if config.DEBUG_MOTOR_CONTROL:
            print("        Warning: %dms pulse, %dms interval" %
                  (config.VIBRATION_PULSE_DURATION, config.VIBRATION_INTERVAL_WARNING))
            print("        Critical: %dms pulse, %dms interval" %
                  (config.VIBRATION_PULSE_DURATION, config.VIBRATION_INTERVAL_CRITICAL))
        print("[Setup] Press button to switch to Control Mode")
        print("=" * 70 + "\n")

    elif mode == "control":
        print("\n" + "=" * 70)
        print("CONTROL MODE - IMU Cursor Control + EMG Click")
        print("=" * 70)
        print("[Setup] IMU Sensor: %s" % config.IMU_TYPE)
        print("[Setup] IMU Calibration: Keep arm still, level")
        if config.DEBUG_CONTROL_MODE:
            print("        Accelerometer & Gyroscope calibration (50 samples each)")
            print("        Complementary filter alpha: %.2f" % config.COMPLEMENTARY_FILTER_ALPHA)
            print("        Cursor speed: %d pixels/degree" % config.CURSOR_SPEED_FACTOR)
        print("[Setup] Control:")
        print("        • Tilt arm FORWARD/BACKWARD (pitch) → Cursor Y movement")
        print("        • Tilt arm LEFT/RIGHT (roll)      → Cursor X movement")
        print("        • Clench FIST (EMG spike)         → Mouse click")
        if config.DEBUG_CONTROL_MODE:
            print("        EMG spike threshold: ADC > %d" % config.EMG_SPIKE_THRESHOLD)
        print("[Setup] Feedback:")
        print("        🟢 Green  = Ready")
        print("        🟡 Yellow = Click detected")
        print("        🔴 Red    = Error (sensor failure)")
        print("[Setup] Press button to switch to Safety Mode")
        print("=" * 70 + "\n")


def main():
    """Main firmware entry point"""
    print_startup_banner()

    if not MODES_AVAILABLE:
        print("[Error] Mode modules not available. Check imports.")
        return

    # Determine initial mode
    current_mode = get_default_mode()
    print(f"[Init] Starting in {current_mode.upper()} mode\n")

    loop_count = 0

    try:
        while True:
            loop_count += 1

            # Print mode info at startup
            print_mode_info(current_mode)

            # Run appropriate mode loop
            if current_mode == "safety":
                if config.DEBUG and config.DEBUG_SAFETY_MODE:
                    print("[Main] Safety Mode loop started")
                next_mode = safety_mode_loop(duration_sec=None)

            elif current_mode == "control":
                if config.DEBUG and config.DEBUG_CONTROL_MODE:
                    print("[Main] Control Mode loop started")
                next_mode = control_mode_loop(duration_sec=None)

            else:
                print(f"[Error] Unknown mode: {current_mode}")
                break

            # Handle mode transition or exit
            if next_mode == "safety":
                current_mode = "safety"
                if config.DEBUG:
                    print(f"\n[Mode] Switching to Safety Mode...\n")
                time.sleep(1)

            elif next_mode == "control":
                current_mode = "control"
                if config.DEBUG:
                    print(f"\n[Mode] Switching to Control Mode...\n")
                time.sleep(1)

            elif next_mode == "stop":
                print(f"\n[Exit] Shutdown requested")
                break

            else:
                print(f"[Error] Unknown mode return: {next_mode}")
                break

            # Safety: prevent infinite fast mode switching
            if loop_count > 100:
                print("[Error] Too many mode switches (safety limit reached)")
                break

    except KeyboardInterrupt:
        print("\n[Stop] Received Ctrl+C interrupt")

    except Exception as e:
        print(f"\n[Error] Unexpected exception: {e}")
        # Traceback import skipped to save memory on ESP32
        # if config.DEBUG:
        #     import traceback
        #     traceback.print_exc()

    finally:
        print("\n[Cleanup] Firmware shutdown")
        print("[Exit] Goodbye!")


if __name__ == "__main__":
    main()
