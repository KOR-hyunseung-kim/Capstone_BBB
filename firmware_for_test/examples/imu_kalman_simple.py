"""
Simple Real-time IMU Kalman Filter for GPIO 8, 9 (I2C)
No complex features - just pure reading and filtering

Usage on ESP32-S3:
    1. Upload this file to /imu_simple.py
    2. Run: python -c "import imu_simple; imu_simple.main()"
    3. Or in REPL: import imu_simple; imu_simple.main()
"""

import math
import time
from machine import I2C, Pin


class SimpleKalmanFilter:
    """Minimal 1D Kalman Filter."""

    def __init__(self, q=0.001, r=0.2):
        self.q = q  # Process noise
        self.r = r  # Measurement noise
        self.x = 0.0  # State
        self.p = 1.0  # Error covariance
        self.k = 0.0  # Kalman gain

    def update(self, measurement):
        """Update with new measurement."""
        self.p = self.p + self.q
        self.k = self.p / (self.p + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1 - self.k) * self.p
        return self.x


class SimpleMPU6050:
    """Minimal MPU6050 driver for GPIO 8, 9."""

    I2C_ADDR = 0x68
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B

    def __init__(self, sda=8, scl=9):
        """Initialize with GPIO 8 (SDA), 9 (SCL)."""
        print(f"[Init] Creating I2C: SDA={sda}, SCL={scl}")
        try:
            self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=100000)
            print("[OK] I2C initialized")
        except Exception as e:
            print(f"[ERROR] I2C init failed: {e}")
            raise

        # Wake up sensor
        try:
            self.i2c.writeto(self.I2C_ADDR, bytes([self.PWR_MGMT_1, 0x00]))
            print("[OK] MPU6050 woken up")
        except Exception as e:
            print(f"[ERROR] MPU6050 write failed: {e}")
            raise

        # Test read
        try:
            data = self.i2c.readfrom_mem(self.I2C_ADDR, self.ACCEL_XOUT_H, 6)
            print(f"[OK] First read successful: {len(data)} bytes")
        except Exception as e:
            print(f"[ERROR] First read failed: {e}")
            raise

    def get_accel(self):
        """Read accelerometer (m/s²)."""
        try:
            data = self.i2c.readfrom_mem(self.I2C_ADDR, self.ACCEL_XOUT_H, 6)
            ax = self._bytes_to_int16(data[0], data[1]) / 16384.0 * 9.81
            ay = self._bytes_to_int16(data[2], data[3]) / 16384.0 * 9.81
            az = self._bytes_to_int16(data[4], data[5]) / 16384.0 * 9.81
            return ax, ay, az
        except Exception as e:
            print(f"[ERROR] Read failed: {e}")
            raise

    @staticmethod
    def _bytes_to_int16(high, low):
        """Convert bytes to int16."""
        value = (high << 8) | low
        if value > 32767:
            value = value - 65536
        return value


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("Simple IMU Kalman Filter Test (GPIO 8, 9)")
    print("=" * 70)

    try:
        # Initialize
        print("\n[Step 1] Initializing IMU...")
        imu = SimpleMPU6050(sda=8, scl=9)

        # Kalman filters
        print("[Step 2] Creating Kalman filters...")
        kf_x = SimpleKalmanFilter(q=0.001, r=0.2)
        kf_y = SimpleKalmanFilter(q=0.001, r=0.2)
        kf_z = SimpleKalmanFilter(q=0.001, r=0.2)

        print("[Step 3] Starting measurements...\n")
        print("-" * 70)
        print("x(m/s²) | y(m/s²) | z(m/s²) | Filtered X")
        print("-" * 70)

        # Read for 10 seconds
        start = time.time()
        count = 0

        while time.time() - start < 10:
            try:
                # Read raw
                ax, ay, az = imu.get_accel()

                # Filter
                ax_f = kf_x.update(ax)
                ay_f = kf_y.update(ay)
                az_f = kf_z.update(az)

                # Print
                print(f"{ax:7.2f} | {ay:7.2f} | {az:7.2f} | {ax_f:7.2f}")

                count += 1
                time.sleep(0.1)

            except Exception as e:
                print(f"[ERROR] Measurement {count}: {e}")
                time.sleep(0.5)
                continue

        print("-" * 70)
        print(f"\n[SUCCESS] Read {count} measurements in 10 seconds")
        print(f"Average rate: {count/10:.1f} Hz")

    except Exception as e:
        print(f"\n[FATAL] {e}")
        print("\nTroubleshooting:")
        print("  1. Check I2C pins: SDA=GPIO8, SCL=GPIO9")
        print("  2. Check MPU6050 power (LED on?)")
        print("  3. Check cable connections")
        print("  4. Try: diagnose_i2c_pins()")


if __name__ == "__main__":
    main()
