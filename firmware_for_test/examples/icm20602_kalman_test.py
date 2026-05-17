"""
ICM-20602 Kalman Filter Real-time Test
Better performance than MPU6050 (lower noise, higher accuracy)

Hardware Connection (I2C mode):
  ICM-20602     ESP32-S3
  ─────────     ────────
  VCC      →    3.3V
  GND      →    GND
  SDA      →    GPIO 8
  SCL      →    GPIO 9
  SAO      →    GND (for address 0x68)
  CS       →    VCC (for I2C mode)
"""

import math
import time
from machine import Pin


class SimpleKalmanFilter:
    """Minimal 1D Kalman Filter."""

    def __init__(self, q=0.0005, r=0.1):
        """Better parameters for ICM-20602 (less noisy)."""
        self.q = q
        self.r = r
        self.x = 0.0
        self.p = 1.0
        self.k = 0.0

    def update(self, measurement):
        """Update with new measurement."""
        self.p = self.p + self.q
        self.k = self.p / (self.p + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1 - self.k) * self.p
        return self.x


def main():
    """Main test function."""
    print("\n" + "=" * 70)
    print("ICM-20602 Kalman Filter Test (GPIO 8, 9)")
    print("=" * 70)

    try:
        # Import sensor
        print("\n[1] Importing ICM-20602 driver...")
        from sensor.icm20602 import ICM20602

        # Initialize
        print("[2] Initializing ICM-20602...")
        imu = ICM20602(sda_pin=8, scl_pin=9)

        # Create Kalman filters (3 axes)
        print("[3] Creating Kalman filters (Q=0.0005, R=0.1)...")
        kf_x = SimpleKalmanFilter(q=0.0005, r=0.1)
        kf_y = SimpleKalmanFilter(q=0.0005, r=0.1)
        kf_z = SimpleKalmanFilter(q=0.0005, r=0.1)

        # Calibration (optional)
        print("[4] Optional: Calibrating (y/n)? ", end="")
        # Skip for auto-testing
        print("n")

        print("\n[5] Starting measurements (30 seconds)...\n")
        print("-" * 80)
        print(
            "Raw X    | Raw Y    | Raw Z    | "
            "Filt X   | Filt Y   | Filt Z   | Temp(C)"
        )
        print("-" * 80)

        # Read for 30 seconds
        start = time.time()
        count = 0
        errors = 0

        while time.time() - start < 30:
            try:
                # Read all data
                ax, ay, az, gx, gy, gz, temp = imu.get_all()

                # Apply Kalman filter
                ax_f = kf_x.update(ax)
                ay_f = kf_y.update(ay)
                az_f = kf_z.update(az)

                # Print log
                print(
                    f"{ax:8.2f} | {ay:8.2f} | {az:8.2f} | "
                    f"{ax_f:8.2f} | {ay_f:8.2f} | {az_f:8.2f} | "
                    f"{temp:6.1f}"
                )

                count += 1
                time.sleep(0.1)  # 100 Hz

            except Exception as e:
                errors += 1
                print(f"[ERROR] Sample {count}: {e}")
                if errors > 5:
                    raise

        print("-" * 80)

        # Summary
        elapsed = time.time() - start
        rate = count / elapsed

        print(f"\n[SUCCESS] Test completed!")
        print(f"  Samples: {count}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Rate: {rate:.1f} Hz")
        print(f"  Errors: {errors}")

        # Performance notes
        print("\n[ICM-20602 Advantages over MPU6050]:")
        print("  ✓ Lower noise")
        print("  ✓ Better temperature stability")
        print("  ✓ Faster sampling rate")
        print("  ✓ Lower power consumption")

    except ImportError as e:
        print(f"\n[ERROR] Cannot import sensor module: {e}")
        print("\nFix:")
        print("  1. Upload firmware/sensor/icm20602.py to ESP32-S3")
        print("  2. Check path: should be /sensor/icm20602.py")

    except RuntimeError as e:
        print(f"\n[ERROR] Sensor error: {e}")
        print("\nFix:")
        print("  1. Check I2C connection: SDA=GPIO8, SCL=GPIO9")
        print("  2. Check SAO pin: GND (for 0x68) or VCC (for 0x69)")
        print("  3. Check CS pin: Pull HIGH to VCC (I2C mode)")
        print("  4. Check power: 3.3V with stable supply")

    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        try:
            traceback.print_exc()
        except:
            print("(traceback not available)")


if __name__ == "__main__":
    main()
