"""
Quick EMG sensor test script
Run directly on ESP32-S3 via Thonny REPL
Usage:
  1. Copy emg.py to ESP32 filesystem
  2. Run this script in Thonny
  3. Observe real-time ADC values and voltage
"""

from emg import EMGSensor
import time

# ESP32-S3 DevKit: MyoWare SIG connected to GPIO1 (ADC1_CH0)
EMG_PIN = 1

print("=" * 50)
print("EMG Quick Test - MyoWare 2.0")
print("=" * 50)

try:
    emg = EMGSensor(adc_pin=EMG_PIN, sample_rate=1000)
    print(f"✓ EMG sensor initialized on GPIO{EMG_PIN}")
    print()

    # Self-test
    emg.test_sensor()
    print()

    # Real-time monitoring loop
    print("Real-time monitoring (Ctrl+C to stop)")
    print("-" * 50)
    print("Time(s)  | ADC Value | Voltage(mV) | Status")
    print("-" * 50)

    start_time = time.time()
    sample_count = 0

    while True:
        elapsed = time.time() - start_time
        adc_val = emg.read_raw()
        mv_val = emg.read_mv()
        is_spike = emg.is_spike(threshold=3500)

        status = "SPIKE!" if is_spike else "normal"
        print(f"{elapsed:7.2f}  | {adc_val:9d} | {mv_val:11.1f} | {status}")

        time.sleep(0.1)
        sample_count += 1

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
