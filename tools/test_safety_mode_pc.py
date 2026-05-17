"""
PC Mock Test for BBB Safety Mode
- EMG 신호 시뮬레이션
- LED/모터 제어 신호를 로그로 출력
- 실제 ESP32 없이 전체 로직 검증
"""

import sys
import time
import math
from pathlib import Path

# Add firmware directory to path
firmware_path = Path(__file__).parent.parent / "firmware"
sys.path.insert(0, str(firmware_path))


# ============================================================================
# Mock Hardware Classes (firmware imports 대체)
# ============================================================================


class MockADC:
    """Mock ADC for EMG sensor"""

    def __init__(self, pin, test_data=None):
        self.pin = pin
        self.test_data = test_data or []
        self.index = 0

    def atten(self, val):
        pass

    def width(self, val):
        pass

    def read(self):
        if self.test_data and self.index < len(self.test_data):
            val = self.test_data[self.index]
            self.index += 1
            return val
        # Simulate noise around 2000
        return int(2000 + 100 * math.sin(self.index * 0.1))


class MockPin:
    """Mock GPIO Pin"""

    OUT = 1

    def __init__(self, pin, mode=None):
        self.pin = pin
        self.mode = mode


class MockPWM:
    """Mock PWM controller"""

    def __init__(self, pin):
        self.pin = pin
        self._duty = 0
        self._freq = 100

    def freq(self, f):
        self._freq = f

    def duty(self, d):
        self._duty = d
        if d > 0:
            print(f"    [PWM] GPIO{self.pin.pin}: duty={d}/1023 ({d*100/1023:.1f}%)")


# Monkey-patch machine module
class MockMachine:
    class ADC:
        ATTN_11DB = 3
        WIDTH_12BIT = 12

        def __init__(self, pin):
            self.adc = MockADC(pin.pin if hasattr(pin, "pin") else pin)

        def atten(self, val):
            self.adc.atten(val)

        def width(self, val):
            self.adc.width(val)

        def read(self):
            return self.adc.read()

    class Pin:
        OUT = 1

        def __init__(self, pin, mode=None):
            self.pin = pin
            self.mode = mode

    class PWM:
        def __init__(self, pin):
            self.pwm = MockPWM(pin)

        def freq(self, f):
            self.pwm.freq(f)

        def duty(self, d):
            self.pwm.duty(d)

    class I2C:
        def __init__(self, id, scl=None, sda=None, freq=None):
            self.id = id
            print(f"[I2C] Initialized I2C-{id} (SDA=GPIO{sda.pin if hasattr(sda, 'pin') else sda}, "
                  f"SCL=GPIO{scl.pin if hasattr(scl, 'pin') else scl}, freq={freq}Hz)")


sys.modules["machine"] = MockMachine()

# Import firmware modules (now with mock machine)
from algo.emg_processor import EMGProcessor, SafetyModeController
from sensor.emg import EMGSensor
from ui.motor import VibratorMotor


# ============================================================================
# Mock EMG Signal Generator
# ============================================================================


class EMGSignalSimulator:
    """Generate realistic EMG signals for testing"""

    def __init__(self, baseline_rms=2000):
        self.baseline_rms = baseline_rms
        self.phase = 0
        self.scenario = "normal"  # normal, fatigue, critical

    def set_scenario(self, scenario):
        """
        Set signal scenario
        - "normal": full strength (2000)
        - "fatigue": 80% (1600)
        - "critical": 60% (1200)
        """
        self.scenario = scenario

    def generate_chunk(self, n_samples=1000, noise_level=100):
        """
        Generate n_samples of EMG signal

        Args:
            n_samples: Number of samples
            noise_level: Gaussian noise std dev

        Returns:
            List of ADC values
        """
        import random

        # Base signal level
        levels = {
            "normal": 2000,
            "fatigue": 1600,
            "critical": 1200,
        }
        base = levels.get(self.scenario, 2000)

        # Generate signal with noise
        samples = []
        for i in range(n_samples):
            # Sine wave + noise
            signal = base + 500 * math.sin(self.phase + i * 0.01)
            noise = random.gauss(0, noise_level)
            sample = int(signal + noise)
            sample = max(0, min(4095, sample))  # Clamp to ADC range
            samples.append(sample)

        self.phase += n_samples * 0.01
        return samples


class MockEMGSensor:
    """Mock EMG sensor with simulated data"""

    def __init__(self, adc_pin=1, sample_rate=1000, signal_sim=None):
        self.adc_pin = adc_pin
        self.sample_rate = sample_rate
        self.signal_sim = signal_sim or EMGSignalSimulator()

    def read_raw(self):
        return int(2000 + 100 * math.sin(time.time()))

    def read_mv(self):
        return self.read_raw() * 3.3 / 4.095

    def sample_chunk(self, n_samples=100):
        return self.signal_sim.generate_chunk(n_samples)

    def is_spike(self, threshold=3500):
        return self.read_raw() > threshold

    def test_sensor(self):
        samples = self.sample_chunk(10)
        avg = sum(samples) / len(samples)
        print(
            f"[EMG] Mock sensor ready: avg={avg:.0f}, range={min(samples)}-{max(samples)}"
        )


class MockVibratorMotor:
    """Mock vibration motor (logs instead of vibrating)"""

    def __init__(self, gpio_pin=38, frequency=100):
        self.gpio_pin = gpio_pin
        self.frequency = frequency
        print(f"[Motor] Initialized on GPIO{gpio_pin} ({frequency}Hz)")

    def single_pulse(self, duration_ms=100, intensity=800):
        print(f"  [Motor] Single pulse: {duration_ms}ms @ {intensity}/1023 intensity")

    def double_pulse(self, interval_ms=150, intensity=900):
        print(f"  [Motor] Double pulse: {intensity}/1023 intensity, {interval_ms}ms interval")

    def continuous(self, duration_ms=500, intensity=1000):
        print(f"  [Motor] Continuous vibration: {duration_ms}ms @ {intensity}/1023 intensity")

    def stop(self):
        print("  [Motor] Stop")

    def alert_pattern(self, level):
        if level == "warning":
            print(f"  [Alert] ⚠️  WARNING pattern")
            self.single_pulse(duration_ms=100, intensity=800)
        elif level == "critical":
            print(f"  [Alert] 🚨 CRITICAL pattern")
            self.continuous(duration_ms=300, intensity=1000)

    def test_vibration(self):
        print("[Motor] Test pattern:")
        for intensity in [400, 600, 800, 1000]:
            print(f"  - Intensity {intensity}/1023")


class MockLED:
    """Mock RGB LED (logs instead of lighting)"""

    colors = {
        "normal": ("🟢", "GREEN"),
        "warning": ("🟡", "YELLOW/ORANGE"),
        "critical": ("🔴", "RED"),
    }

    def __init__(self, red_pin=17, green_pin=18, blue_pin=19, frequency=1000):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        print(f"[LED] RGB initialized: R=GPIO{red_pin}, G=GPIO{green_pin}, B=GPIO{blue_pin}")

    def set_color(self, level):
        emoji, color = self.colors.get(level, ("⚪", "UNKNOWN"))
        print(f"  [LED] {emoji} {color} ({level})")

    def off(self):
        print("  [LED] OFF")

    def set_rgb(self, r, g, b):
        print(f"  [LED] RGB({r}, {g}, {b})")


class MockOLED:
    """Mock OLED display"""

    def __init__(self, i2c=None):
        print("[OLED] Mock display initialized")

    def update(self, data):
        fatigue = data.get("fatigue_pct", 0)
        level = data.get("level", "normal")
        print(f"  [OLED] Fatigue: {fatigue:5.1f}% | Status: {level.upper()}")

    def clear(self):
        print("  [OLED] Clear")


# ============================================================================
# Test Scenarios
# ============================================================================


def test_scenario_normal_to_critical():
    """
    Scenario: 정상 → 주의 → 경고 상태 변화 시뮬레이션
    """
    print("\n" + "=" * 70)
    print("TEST: Normal → Warning → Critical Progression")
    print("=" * 70)

    # Setup
    signal_sim = EMGSignalSimulator(baseline_rms=2000)
    emg = MockEMGSensor(signal_sim=signal_sim)
    motor = MockVibratorMotor()
    led = MockLED()
    oled = MockOLED()

    processor = EMGProcessor(emg_sensor=emg, vibrator=motor)
    controller = SafetyModeController(
        emg_processor=processor,
        led_controller=led,
        oled_display=oled,
    )

    # Calibration
    print("\n[Step 1] CALIBRATION (60 samples = simulated 1 minute)")
    if not controller.start(duration_sec=60):
        print("Calibration failed!")
        return

    baseline = processor.baseline_rms
    print(f"✓ Baseline RMS: {baseline:.1f}")

    # Monitoring with scenario changes
    scenarios = [
        ("normal", 10, "정상 상태 유지"),
        ("fatigue", 10, "피로도 증가 (80%)"),
        ("critical", 10, "심각한 피로 (60%)"),
        ("normal", 10, "회복 단계"),
    ]

    print("\n[Step 2] MONITORING LOOP")
    for scenario, duration, description in scenarios:
        print(f"\n--- Phase: {description} ({scenario.upper()}) ---")
        signal_sim.set_scenario(scenario)

        for i in range(duration):
            rms, level = controller.run_once()
            signal_pct = (rms / baseline) * 100

            if i % 3 == 0:  # Log every 3 cycles
                level_emoji = {"normal": "✓", "warning": "⚠", "critical": "✕"}.get(
                    level, "?"
                )
                print(
                    f"  [{i+1:2d}s] {level_emoji} RMS={rms:6.1f} ({signal_pct:5.1f}%) → {level.upper()}"
                )

            time.sleep(0.01)

    controller.stop()
    print("\n✓ Test completed\n")


def test_scenario_fatigue_threshold():
    """
    Scenario: 임계값 정확성 검증 (90%, 70%)
    """
    print("\n" + "=" * 70)
    print("TEST: Fatigue Threshold Validation (90%, 70%)")
    print("=" * 70)

    signal_sim = EMGSignalSimulator(baseline_rms=1000)
    emg = MockEMGSensor(signal_sim=signal_sim)
    motor = MockVibratorMotor()
    led = MockLED()

    processor = EMGProcessor(emg_sensor=emg, vibrator=motor)
    controller = SafetyModeController(
        emg_processor=processor,
        led_controller=led,
    )

    # Calibration
    print("\n[Calibration]")
    controller.start(duration_sec=60)
    baseline = processor.baseline_rms
    print(f"✓ Baseline: {baseline:.1f}")

    # Test specific RMS values
    test_points = [
        (950, 95, "normal", "✓"),  # 95% - normal
        (920, 92, "normal", "✓"),  # 92% - normal
        (900, 90, "normal", "✓"),  # 90% - boundary (normal)
        (850, 85, "warning", "⚠"),  # 85% - warning
        (750, 75, "warning", "⚠"),  # 75% - warning
        (700, 70, "warning", "⚠"),  # 70% - boundary (warning)
        (650, 65, "critical", "✕"),  # 65% - critical
        (500, 50, "critical", "✕"),  # 50% - critical
    ]

    print("\n[Threshold Tests]")
    print("RMS  | % Base | Expected | Got | Result")
    print("-" * 50)

    for rms, pct, expected_level, emoji in test_points:
        level, _ = processor.get_fatigue_level(rms)
        result = "✅" if level == expected_level else "❌"
        print(
            f"{rms:4.0f} | {pct:5.0f}% | {expected_level:8s} | {level:8s} | {result}"
        )

    controller.stop()
    print("\n✓ Threshold validation completed\n")


def test_scenario_realtime_monitoring():
    """
    Scenario: 실시간 모니터링 시뮬레이션 (10초)
    """
    print("\n" + "=" * 70)
    print("TEST: Real-time Monitoring (10 seconds)")
    print("=" * 70)

    signal_sim = EMGSignalSimulator(baseline_rms=2000)
    emg = MockEMGSensor(signal_sim=signal_sim)
    motor = MockVibratorMotor()
    led = MockLED()
    oled = MockOLED()

    processor = EMGProcessor(emg_sensor=emg, vibrator=motor)
    controller = SafetyModeController(
        emg_processor=processor,
        led_controller=led,
        oled_display=oled,
    )

    # Calibration
    print("\n[Calibration Phase]")
    signal_sim.set_scenario("normal")
    if not controller.start(duration_sec=60):
        return

    baseline = processor.baseline_rms
    print(f"✓ Baseline: {baseline:.1f}")

    # Monitoring
    print("\n[Monitoring - 10 seconds with gradual fatigue]")
    print("Simulating progressive fatigue increase...")

    start_time = time.time()
    while time.time() - start_time < 10:
        elapsed = time.time() - start_time

        # Gradually increase fatigue
        if elapsed < 3:
            signal_sim.set_scenario("normal")
        elif elapsed < 6:
            signal_sim.set_scenario("fatigue")
        else:
            signal_sim.set_scenario("critical")

        rms, level = controller.run_once()
        signal_pct = (rms / baseline) * 100

        if int(elapsed) % 2 == 0 and elapsed % 1 < 0.05:  # Log every 2 sec
            emoji = {"normal": "✓", "warning": "⚠", "critical": "✕"}.get(level, "?")
            print(
                f"[{elapsed:5.1f}s] {emoji} RMS={rms:6.1f} ({signal_pct:5.1f}%) → {level.upper()}"
            )

        time.sleep(0.01)

    controller.stop()
    print("\n✓ Real-time monitoring completed\n")


# ============================================================================
# Main Test Runner
# ============================================================================


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("BBB Safety Mode - PC Mock Test Suite")
    print("Testing EMG fatigue detection with simulated signals")
    print("=" * 70)

    try:
        # Run test scenarios
        test_scenario_fatigue_threshold()
        test_scenario_normal_to_critical()
        test_scenario_realtime_monitoring()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Review the log output above to verify LED/Motor control signals")
        print("2. If results look correct, proceed to ESP32-S3 hardware setup")
        print("3. See STAGE 2 instructions for real hardware testing")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
