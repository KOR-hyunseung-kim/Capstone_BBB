"""
Real-time IMU Kalman Filter Visualization
Reads MPU6050 (x,y,z acceleration) with Kalman filtering
Displays: pitch, roll, and filtered acceleration in real-time

Usage:
    1. Upload to ESP32-S3
    2. Run: python -m main (or import and call run())
    3. View output in serial monitor
"""

import math
import time
from machine import I2C, Pin

# Import sensor and filter
import sys
sys.path.insert(0, '/firmware')

from sensor.imu import MPU6050
from algo.kalman_filter import KalmanFilter3D


class IMUKalmanFilter:
    """Real-time IMU reading with Kalman filtering and tilt estimation."""

    def __init__(self, sample_rate=100):
        """
        Initialize IMU with Kalman filter.

        Args:
            sample_rate: Sampling frequency in Hz
        """
        print("Initializing MPU6050...")
        self.imu = MPU6050(sda_pin=21, scl_pin=22)

        # 3D Kalman filter for accelerometer
        self.kf = KalmanFilter3D(
            process_variance=0.001,
            measurement_variance=0.2,
        )

        self.sample_rate = sample_rate
        self.sample_interval = 1.0 / sample_rate

        # Complementary filter for gyro/accel fusion
        self.alpha = 0.95  # Accel influence (0-1)
        self.pitch = 0.0  # rad
        self.roll = 0.0  # rad

        # Calibration
        print("\nCalibrating sensors...")
        self.imu.calibrate_accel(samples=50)
        self.imu.calibrate_gyro(samples=50)

        print("\nIMU ready!")
        print("=" * 60)

    def calculate_tilt(self, ax, ay, az):
        """
        Calculate pitch and roll from accelerometer.

        Args:
            ax, ay, az: Acceleration in m/s²

        Returns:
            (pitch_deg, roll_deg)
        """
        # Pitch: rotation around Y axis
        pitch = math.atan2(ax, math.sqrt(ay * ay + az * az))

        # Roll: rotation around X axis
        roll = math.atan2(ay, math.sqrt(ax * ax + az * az))

        # Convert to degrees
        pitch_deg = math.degrees(pitch)
        roll_deg = math.degrees(roll)

        return pitch_deg, roll_deg

    def complementary_filter(self, ax, ay, az, gx, gy, gz):
        """
        Complementary filter: fuse accelerometer and gyroscope data.

        Args:
            ax, ay, az: Filtered acceleration (m/s²)
            gx, gy, gz: Gyroscope data (deg/s)

        Returns:
            (pitch_deg, roll_deg)
        """
        # Convert gyro to radians per second
        gx_rad = math.radians(gx)
        gy_rad = math.radians(gy)

        # Integrate gyro over dt
        dt = self.sample_interval
        self.pitch += gx_rad * dt
        self.roll += gy_rad * dt

        # Get accelerometer-based tilt
        accel_pitch, accel_roll = self.calculate_tilt(ax, ay, az)
        accel_pitch_rad = math.radians(accel_pitch)
        accel_roll_rad = math.radians(accel_roll)

        # Complementary filter
        self.pitch = (
            self.alpha * self.pitch + (1 - self.alpha) * accel_pitch_rad
        )
        self.roll = (
            self.alpha * self.roll + (1 - self.alpha) * accel_roll_rad
        )

        return math.degrees(self.pitch), math.degrees(self.roll)

    def format_log(
        self, pitch, roll, ax, ay, az, gx, gy, gz, temp
    ):
        """Format sensor data as log string."""
        return (
            f"pitch:{pitch:6.1f}d roll:{roll:6.1f}d | "
            f"ax:{ax:6.2f} ay:{ay:6.2f} az:{az:6.2f} | "
            f"gx:{gx:7.1f} gy:{gy:7.1f} gz:{gz:7.1f} | "
            f"T:{temp:5.1f}C"
        )

    def run(self, duration=0, verbose=True):
        """
        Run real-time IMU reading loop.

        Args:
            duration: Run duration in seconds (0 = infinite)
            verbose: Print detailed logs
        """
        print("\nStarting real-time sensor reading...")
        print(
            "pitch(deg) roll(deg) | "
            "ax(m/s²) ay(m/s²) az(m/s²) | "
            "gx(deg/s) gy(deg/s) gz(deg/s) | temp(C)"
        )
        print("=" * 80)

        start_time = time.time()
        sample_count = 0

        try:
            while True:
                sample_start = time.time()

                # Read sensor data
                ax, ay, az, gx, gy, gz, temp = self.imu.get_all()

                # Apply Kalman filter to accelerometer
                ax_f, ay_f, az_f = self.kf.update(ax, ay, az)

                # Complementary filter for tilt estimation
                pitch, roll = self.complementary_filter(
                    ax_f, ay_f, az_f, gx, gy, gz
                )

                # Format and print log
                log = self.format_log(
                    pitch, roll, ax_f, ay_f, az_f, gx, gy, gz, temp
                )
                if verbose:
                    print(log)

                sample_count += 1

                # Check duration
                if duration > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        break

                # Maintain sample rate
                elapsed_sample = time.time() - sample_start
                if elapsed_sample < self.sample_interval:
                    time.sleep(self.sample_interval - elapsed_sample)

        except KeyboardInterrupt:
            print("\nStopped by user")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

        # Print summary
        if sample_count > 0:
            elapsed_total = time.time() - start_time
            actual_rate = sample_count / elapsed_total
            print("=" * 80)
            print(
                f"\nSummary: {sample_count} samples in {elapsed_total:.1f}s "
                f"({actual_rate:.1f} Hz)"
            )


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("BBB - Real-time IMU Kalman Filter Demo")
    print("=" * 60)

    try:
        # Initialize
        sensor = IMUKalmanFilter(sample_rate=100)

        # Run for 30 seconds (0 = infinite)
        sensor.run(duration=30, verbose=True)

    except Exception as e:
        print(f"Failed to initialize: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
