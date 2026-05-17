"""
Kalman Filter Tests for MicroPython (ESP32-S3)
Tests pure Kalman filtering + Real-time IMU with complementary filter
Simple test runner without pytest - runs on device directly

Usage on ESP32-S3:
    import test_kalman_micropython
    test_kalman_micropython.run_all_tests()
    # or for real-time IMU:
    test_kalman_micropython.run_imu_realtime()
"""

import math
import time
import sys

try:
    from machine import I2C, Pin
    MICROPYTHON = True
except ImportError:
    MICROPYTHON = False

# traceback module compatibility
try:
    import traceback
except ImportError:
    # MicroPython doesn't have traceback, use simple version
    class traceback:
        @staticmethod
        def print_exc():
            print("Error occurred (traceback not available in MicroPython)")


class KalmanFilter1D:
    """1D Kalman Filter for single-axis acceleration filtering."""

    def __init__(
        self,
        process_variance=0.01,
        measurement_variance=0.1,
        initial_value=0.0,
        initial_estimate_error=1.0,
    ):
        """Initialize 1D Kalman Filter."""
        self.q = process_variance
        self.r = measurement_variance
        self.x = initial_value
        self.p = initial_estimate_error
        self.k = 0.0

    def update(self, measurement):
        """Update filter with new measurement."""
        self.p = self.p + self.q
        self.k = self.p / (self.p + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1 - self.k) * self.p
        return self.x

    def reset(self, initial_value=0.0):
        """Reset filter state."""
        self.x = initial_value
        self.p = 1.0
        self.k = 0.0


class KalmanFilter3D:
    """3D Kalman Filter for accelerometer (ax, ay, az)."""

    def __init__(
        self,
        process_variance=0.01,
        measurement_variance=0.1,
    ):
        """Initialize 3D Kalman Filter."""
        self.filter_x = KalmanFilter1D(process_variance, measurement_variance)
        self.filter_y = KalmanFilter1D(process_variance, measurement_variance)
        self.filter_z = KalmanFilter1D(process_variance, measurement_variance)

    def update(self, ax, ay, az):
        """Update filter with 3-axis measurement."""
        return (
            self.filter_x.update(ax),
            self.filter_y.update(ay),
            self.filter_z.update(az),
        )

    def reset(self):
        """Reset all axis filters."""
        self.filter_x.reset()
        self.filter_y.reset()
        self.filter_z.reset()


class AdaptiveKalmanFilter1D:
    """Adaptive Kalman Filter with self-tuning measurement variance."""

    def __init__(
        self,
        process_variance=0.01,
        base_measurement_variance=0.1,
        adaptation_rate=0.01,
    ):
        """Initialize Adaptive 1D Kalman Filter."""
        self.q = process_variance
        self.r_base = base_measurement_variance
        self.r = base_measurement_variance
        self.x = 0.0
        self.p = 1.0
        self.k = 0.0
        self.adaptation_rate = adaptation_rate
        self.residuals = []
        self.max_residuals = 50

    def update(self, measurement):
        """Update with adaptive measurement variance."""
        self.p = self.p + self.q
        self.k = self.p / (self.p + self.r)
        residual = measurement - self.x
        self.x = self.x + self.k * residual
        self.p = (1 - self.k) * self.p

        self.residuals.append(residual * residual)
        if len(self.residuals) > self.max_residuals:
            self.residuals.pop(0)

        if len(self.residuals) >= 10:
            mean_sq_residual = sum(self.residuals) / len(self.residuals)
            self.r = (
                (1 - self.adaptation_rate) * self.r
                + self.adaptation_rate * mean_sq_residual
            )
            self.r = max(self.r, self.r_base * 0.5)

        return self.x


# ============================================================================
# Test Suite
# ============================================================================


def assert_equal(actual, expected, tolerance=0.0001, msg=""):
    """Assert with tolerance for floating point."""
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"{msg}\nExpected: {expected}, Got: {actual}"
        )


def assert_true(condition, msg=""):
    """Assert condition is true."""
    if not condition:
        raise AssertionError(msg)


def assert_less(actual, limit, msg=""):
    """Assert actual < limit."""
    if actual >= limit:
        raise AssertionError(f"{msg}\nExpected < {limit}, Got: {actual}")


def assert_greater(actual, limit, msg=""):
    """Assert actual > limit."""
    if actual <= limit:
        raise AssertionError(f"{msg}\nExpected > {limit}, Got: {actual}")


def test_1d_initialization():
    """Test 1D filter initialization."""
    kf = KalmanFilter1D(
        process_variance=0.01,
        measurement_variance=0.1,
        initial_value=5.0,
    )
    assert_equal(kf.x, 5.0, msg="Initial value mismatch")
    assert_equal(kf.p, 1.0, msg="Initial error mismatch")
    assert_equal(kf.q, 0.01, msg="Process variance mismatch")
    assert_equal(kf.r, 0.1, msg="Measurement variance mismatch")
    print("  [OK] 1D Initialization")


def test_1d_constant_value():
    """Test filter converges to constant input."""
    kf = KalmanFilter1D(
        process_variance=0.001, measurement_variance=1.0
    )
    true_value = 9.81
    measurements = [true_value + 0.5 * math.sin(i * 0.1) for i in range(100)]

    estimates = [kf.update(m) for m in measurements]

    assert_less(
        abs(estimates[-1] - true_value),
        0.2,
        "Filter did not converge to true value",
    )
    print("  [OK] 1D Constant Value Convergence")


def test_1d_noise_reduction():
    """Test filter reduces measurement noise."""
    kf = KalmanFilter1D(process_variance=0.001, measurement_variance=0.5)
    true_value = 5.0
    noise_std = 2.0
    measurements = [
        true_value + noise_std * math.sin(i) for i in range(200)
    ]

    estimates = [kf.update(m) for m in measurements]

    raw_var = sum((m - true_value) ** 2 for m in measurements[-50:]) / 50
    est_var = sum((e - true_value) ** 2 for e in estimates[-50:]) / 50

    assert_less(est_var, raw_var, "Filter did not reduce variance")
    print("  [OK] 1D Noise Reduction")


def test_1d_step_response():
    """Test filter responds to step change."""
    kf = KalmanFilter1D(
        process_variance=0.01, measurement_variance=0.1
    )
    measurements = [0.0] * 50 + [10.0] * 50

    estimates = [kf.update(m) for m in measurements]

    assert_less(estimates[49], 5.0, "Step rise too fast")
    assert_greater(estimates[99], 8.0, "Step response incomplete")
    print("  [OK] 1D Step Response")


def test_1d_reset():
    """Test filter reset."""
    kf = KalmanFilter1D(initial_value=0.0)
    kf.update(5.0)
    kf.update(5.0)
    assert_true(kf.x != 0.0, "Filter did not update")

    kf.reset(0.0)
    assert_equal(kf.x, 0.0, msg="Reset failed")
    assert_equal(kf.p, 1.0, msg="Reset error covariance failed")
    print("  [OK] 1D Reset")


def test_1d_gain_convergence():
    """Test Kalman gain stabilizes."""
    kf = KalmanFilter1D(
        process_variance=0.001, measurement_variance=0.1
    )
    measurements = [5.0] * 100

    gains = []
    for m in measurements:
        kf.update(m)
        gains.append(kf.k)

    assert_greater(gains[0], gains[-1], "Gain did not decrease")
    assert_less(
        abs(gains[-1] - gains[-2]),
        0.0001,
        "Gain did not stabilize",
    )
    print("  [OK] 1D Gain Convergence")


def test_3d_initialization():
    """Test 3D filter initialization."""
    kf = KalmanFilter3D(
        process_variance=0.01, measurement_variance=0.1
    )
    assert_true(
        kf.filter_x is not None, "X filter not initialized"
    )
    assert_true(
        kf.filter_y is not None, "Y filter not initialized"
    )
    assert_true(
        kf.filter_z is not None, "Z filter not initialized"
    )
    print("  [OK] 3D Initialization")


def test_3d_filtering():
    """Test 3D filter processes all axes."""
    kf = KalmanFilter3D(
        process_variance=0.001, measurement_variance=0.5
    )

    measurements = [
        (
            9.81 + 0.2 * math.sin(i * 0.1),
            0.1 * math.cos(i * 0.1),
            -0.3,
        )
        for i in range(100)
    ]

    estimates = [kf.update(ax, ay, az) for ax, ay, az in measurements]

    ax_est, ay_est, az_est = estimates[-1]
    assert_less(
        abs(ax_est - 9.81), 0.3, "X axis filtering failed"
    )
    assert_less(
        abs(ay_est - 0.0), 0.3, "Y axis filtering failed"
    )
    assert_less(
        abs(az_est - (-0.3)), 0.3, "Z axis filtering failed"
    )
    print("  [OK] 3D Filtering")


def test_3d_independence():
    """Test axes filter independently."""
    kf = KalmanFilter3D(
        process_variance=0.001, measurement_variance=0.1
    )

    high_noise_x = [5.0 + 5.0 * math.sin(i * 0.5) for i in range(100)]

    estimates = [kf.update(high_noise_x[i], 0.0, 0.0) for i in range(100)]

    _, y_final, z_final = estimates[-1]
    assert_less(abs(y_final), 0.1, "Y axis affected by X noise")
    assert_less(abs(z_final), 0.1, "Z axis affected by X noise")
    print("  [OK] 3D Independence")


def test_adaptive_initialization():
    """Test adaptive filter initialization."""
    kf = AdaptiveKalmanFilter1D(
        process_variance=0.01,
        base_measurement_variance=0.1,
        adaptation_rate=0.05,
    )
    assert_equal(kf.r, 0.1, msg="Initial variance mismatch")
    assert_equal(
        kf.adaptation_rate, 0.05, msg="Adaptation rate mismatch"
    )
    print("  [OK] Adaptive Initialization")


def test_adaptive_noise_increase():
    """Test filter adapts to increasing noise."""
    kf = AdaptiveKalmanFilter1D(
        process_variance=0.001,
        base_measurement_variance=0.1,
        adaptation_rate=0.1,
    )

    low_noise_meas = [5.0 + 0.1 * math.sin(i) for i in range(50)]
    high_noise_meas = [5.0 + 2.0 * math.sin(i) for i in range(50)]

    for m in low_noise_meas:
        kf.update(m)
    r_low_noise = kf.r

    for m in high_noise_meas:
        kf.update(m)
    r_high_noise = kf.r

    assert_greater(r_high_noise, r_low_noise, "Filter did not adapt to noise")
    print("  [OK] Adaptive Noise Increase")


def test_adaptive_residuals():
    """Test residual tracking."""
    kf = AdaptiveKalmanFilter1D(
        process_variance=0.001,
        base_measurement_variance=0.1,
        adaptation_rate=0.1,
    )

    measurements = [5.0 + 0.5 * math.sin(i) for i in range(100)]
    for m in measurements:
        kf.update(m)

    assert_true(
        len(kf.residuals) > 0, "No residuals tracked"
    )
    assert_less(
        len(kf.residuals),
        kf.max_residuals + 1,
        "Residuals not capped",
    )
    print("  [OK] Adaptive Residuals")


def test_gravity_filtering():
    """Test gravity measurement filtering."""
    kf = KalmanFilter1D(
        process_variance=0.001, measurement_variance=0.2
    )

    true_gravity = 9.81
    noise_std = 0.5
    measurements = [
        true_gravity + noise_std * math.sin(i * 0.05) for i in range(200)
    ]

    estimates = [kf.update(m) for m in measurements]

    assert_less(
        abs(estimates[-1] - true_gravity),
        0.2,
        "Gravity filtering failed",
    )
    print("  [OK] Gravity Measurement Filtering")


def test_dynamic_acceleration():
    """Test dynamic acceleration tracking."""
    kf = KalmanFilter1D(
        process_variance=0.01, measurement_variance=0.2
    )

    accel_profile = (
        [0.0] * 30
        + [i * 0.5 for i in range(20)]
        + [10.0] * 30
        + [10.0 - i * 0.3 for i in range(20)]
    )

    estimates = [kf.update(a) for a in accel_profile]

    assert_less(estimates[29], 2.0, "Early phase tracking failed")
    assert_greater(estimates[59], 8.0, "Middle phase tracking failed")
    assert_greater(estimates[79], 6.0, "Late phase tracking failed")
    print("  [OK] Dynamic Acceleration Tracking")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("KALMAN FILTER MICROPYTHON TEST SUITE")
    print("=" * 60)

    tests = [
        ("1D Filter", [
            test_1d_initialization,
            test_1d_constant_value,
            test_1d_noise_reduction,
            test_1d_step_response,
            test_1d_reset,
            test_1d_gain_convergence,
        ]),
        ("3D Filter", [
            test_3d_initialization,
            test_3d_filtering,
            test_3d_independence,
        ]),
        ("Adaptive Filter", [
            test_adaptive_initialization,
            test_adaptive_noise_increase,
            test_adaptive_residuals,
        ]),
        ("Integration Tests", [
            test_gravity_filtering,
            test_dynamic_acceleration,
        ]),
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for category, test_list in tests:
        print(f"\n{category}:")
        for test_func in test_list:
            total_tests += 1
            try:
                test_func()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append((test_func.__name__, str(e)))
                print(f"  [FAIL] {test_func.__name__}")
                print(f"    {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if failed_tests:
        print("\nFailed Tests:")
        for name, error in failed_tests:
            print(f"  - {name}: {error}")
        return False
    else:
        print("\n[PASS] All tests passed!")
        return True


# ============================================================================
# Real-time IMU Testing (ESP32-S3 only)
# ============================================================================


def diagnose_i2c_pins():
    """Diagnose I2C pins and find MPU6050."""
    if not MICROPYTHON:
        print("[SKIP] I2C diagnosis only works on MicroPython")
        return False

    print("\n" + "=" * 70)
    print("I2C PIN DIAGNOSIS")
    print("=" * 70)

    from machine import I2C, Pin

    # Common I2C pin combinations for ESP32-S3
    pin_combinations = [
        (21, 22, "Default (GPIO21=SDA, GPIO22=SCL)"),
        (20, 21, "Alternative 1"),
        (6, 7, "Alternative 2"),
        (8, 9, "Alternative 3"),
        (4, 5, "Alternative 4"),
    ]

    print("\nTesting I2C pin combinations...")
    print("-" * 70)

    found_device = False

    for sda, scl, description in pin_combinations:
        try:
            i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)
            devices = i2c.scan()

            status = "OK"
            device_info = ""

            if devices:
                device_info = f" - Found: {[hex(d) for d in devices]}"
                if 0x68 in devices:  # MPU6050 address
                    device_info += " ← MPU6050 detected!"
                    found_device = True
                    status = "SUCCESS"

            print(
                f"  SDA={sda:2d} SCL={scl:2d} "
                f"({description:20s}): [{status}]{device_info}"
            )

        except ValueError as e:
            print(
                f"  SDA={sda:2d} SCL={scl:2d} "
                f"({description:20s}): [INVALID PIN]"
            )
        except Exception as e:
            print(
                f"  SDA={sda:2d} SCL={scl:2d} "
                f"({description:20s}): [ERROR] {e}"
            )

    print("-" * 70)

    if found_device:
        print("\n[SUCCESS] MPU6050 found at 0x68!")
        print("Use: imu = MPU6050(sda_pin=21, scl_pin=22)")
        return True
    else:
        print("\n[WARNING] MPU6050 not found (0x68)")
        print("\nChecklist:")
        print("  [ ] MPU6050 power supply (3.3V or 5V)")
        print("  [ ] I2C cable connections")
        print("  [ ] Pull-up resistors (4.7kΩ optional)")
        print("  [ ] Check for I2C address conflicts")
        return False


def test_imu_kalman_realtime(duration=30, sample_rate=50, sda_pin=21, scl_pin=22):
    """
    Real-time IMU Kalman filter test on ESP32-S3.

    Displays: pitch, roll, x, y, z acceleration with log format

    Args:
        duration: Test duration in seconds
        sample_rate: Sampling frequency in Hz
    """
    if not MICROPYTHON:
        print("[SKIP] IMU test requires MicroPython on ESP32-S3")
        return False

    print("\n" + "=" * 70)
    print("REAL-TIME IMU KALMAN FILTER TEST")
    print("=" * 70)

    try:
        # Import IMU driver
        try:
            from sensor.imu import MPU6050
        except ImportError:
            print("[ERROR] sensor.imu module not found")
            print("Please upload firmware/sensor/imu.py to ESP32-S3")
            return False

        print(f"\n[1] Initializing MPU6050 sensor (SDA={sda_pin}, SCL={scl_pin})...")
        imu = MPU6050(sda_pin=sda_pin, scl_pin=scl_pin)

        print("[2] Calibrating sensors...")
        imu.calibrate_accel(samples=30)
        imu.calibrate_gyro(samples=30)

        print("[3] Starting real-time measurement...")
        print(
            "pitch(d) roll(d) | "
            "x(m/s2) y(m/s2) z(m/s2) | "
            "gx(d/s) gy(d/s) gz(d/s) | T(C)"
        )
        print("-" * 70)

        # Initialize Kalman filter
        kf = KalmanFilter3D(
            process_variance=0.001,
            measurement_variance=0.2,
        )

        # Complementary filter state
        alpha = 0.95
        pitch = 0.0
        roll = 0.0
        sample_interval = 1.0 / sample_rate

        start_time = time.time()
        sample_count = 0

        while True:
            sample_start = time.time()

            # Get sensor data
            ax, ay, az, gx, gy, gz, temp = imu.get_all()

            # Apply Kalman filter to accelerometer
            ax_f, ay_f, az_f = kf.update(ax, ay, az)

            # Complementary filter: fuse gyro + accel
            gx_rad = math.radians(gx)
            gy_rad = math.radians(gy)

            dt = sample_interval
            pitch += gx_rad * dt
            roll += gy_rad * dt

            accel_pitch = math.atan2(
                ax_f, math.sqrt(ay_f * ay_f + az_f * az_f)
            )
            accel_roll = math.atan2(
                ay_f, math.sqrt(ax_f * ax_f + az_f * az_f)
            )

            pitch = alpha * pitch + (1 - alpha) * accel_pitch
            roll = alpha * roll + (1 - alpha) * accel_roll

            pitch_deg = math.degrees(pitch)
            roll_deg = math.degrees(roll)

            # Format log
            log = (
                f"pitch:{pitch_deg:6.1f} roll:{roll_deg:6.1f} | "
                f"x:{ax_f:6.2f} y:{ay_f:6.2f} z:{az_f:6.2f} | "
                f"gx:{gx:7.1f} gy:{gy:7.1f} gz:{gz:7.1f} | "
                f"T:{temp:5.1f}"
            )
            print(log)

            sample_count += 1

            # Check duration
            if time.time() - start_time >= duration:
                break

            # Maintain sample rate
            elapsed = time.time() - sample_start
            if elapsed < sample_interval:
                time.sleep(sample_interval - elapsed)

        print("-" * 70)
        elapsed_total = time.time() - start_time
        actual_rate = sample_count / elapsed_total

        print(
            f"\nCompleted: {sample_count} samples in {elapsed_total:.1f}s "
            f"({actual_rate:.1f} Hz)"
        )
        print("[SUCCESS] Real-time IMU test passed!")
        return True

    except KeyboardInterrupt:
        print("\nStopped by user")
        return False
    except OSError as e:
        print(f"\n[ERROR] I2C Communication failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check I2C pin connection (21=SDA, 22=SCL)")
        print("  2. Check MPU6050 power supply (3.3V or 5V)")
        print("  3. Check for pull-up resistors (4.7kΩ)")
        print("  4. Verify MPU6050 I2C address (0x68)")
        return False
    except ValueError as e:
        print(f"\n[ERROR] Pin configuration error: {e}")
        print("\nFor ESP32-S3, use:")
        print("  imu = MPU6050(sda_pin=21, scl_pin=22)")
        return False
    except Exception as e:
        print(f"\n[ERROR] IMU test failed: {e}")
        traceback.print_exc()
        return False


def main_menu():
    """Interactive menu for running tests."""
    print("\n" + "=" * 70)
    print("KALMAN FILTER & IMU TEST MENU (ESP32-S3)")
    print("=" * 70)
    print("\nOptions:")
    print("  0 - Diagnose I2C pins & MPU6050 connection")
    print("  1 - Run all Kalman filter unit tests (14 tests)")
    print("  2 - Run real-time IMU with Kalman filter (30 seconds)")
    print("  3 - Run both tests")
    print("  9 - Exit")

    choice = input("\nSelect [0-3, 9]: ").strip()

    if choice == "0":
        return diagnose_i2c_pins()
    elif choice == "1":
        return run_all_tests()
    elif choice == "2":
        return test_imu_kalman_realtime(duration=30, sample_rate=50)
    elif choice == "3":
        result1 = run_all_tests()
        result2 = test_imu_kalman_realtime(duration=20, sample_rate=50)
        return result1 and result2
    else:
        print("Exiting...")
        return True


if __name__ == "__main__":
    try:
        if MICROPYTHON:
            # On ESP32-S3: show menu
            main_menu()
        else:
            # On PC: just run unit tests
            success = run_all_tests()
            if success:
                print("\n[SUCCESS] Kalman Filter ready for deployment")
                print("\nTo test on ESP32-S3, run:")
                print("  import test_kalman_micropython")
                print("  test_kalman_micropython.test_imu_kalman_realtime()")
            else:
                print("\n[ERROR] Some tests failed")
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {e}")
        import traceback
        traceback.print_exc()
