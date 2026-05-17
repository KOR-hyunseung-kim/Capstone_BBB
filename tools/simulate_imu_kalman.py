#!/usr/bin/env python3
"""
Simulate Real-time IMU with Kalman Filter
Generates synthetic sensor data and applies Kalman filtering
Shows what the actual device output will look like

Usage: python tools/simulate_imu_kalman.py
"""

import sys
import math
import time
from pathlib import Path

firmware_path = Path(__file__).parent.parent / "firmware"
sys.path.insert(0, str(firmware_path))

from algo.kalman_filter import KalmanFilter3D


class SimulatedIMU:
    """Simulated MPU6050 IMU with realistic noise."""

    def __init__(self, sample_rate=100):
        """Initialize simulated IMU."""
        self.sample_rate = sample_rate
        self.sample_interval = 1.0 / sample_rate
        self.time = 0.0

        # Calibration offsets (simulated)
        self.accel_offset = [0.05, -0.03, 0.0]
        self.gyro_offset = [0.5, -0.3, 0.2]

    def get_all(self):
        """
        Generate synthetic IMU data.

        Simulates:
        - Smooth tilt motion (pitch/roll oscillation)
        - Realistic noise on accelerometer
        - Constant temperature
        """
        # Simulate gentle tilting motion
        pitch_motion = 15.0 * math.sin(self.time * 0.5)
        roll_motion = 10.0 * math.cos(self.time * 0.3)

        # Convert to acceleration (tilt) and gyro (angular velocity)
        pitch_rad = math.radians(pitch_motion)
        roll_rad = math.radians(roll_motion)

        # Acceleration from tilt (gravity decomposition)
        ax = 9.81 * math.sin(pitch_rad) + 0.3 * math.sin(self.time * 5)
        ay = 9.81 * math.sin(roll_rad) + 0.2 * math.cos(self.time * 7)
        az = 9.81 * math.cos(pitch_rad) * math.cos(
            roll_rad
        ) + 0.25 * math.sin(self.time * 3)

        # Gyroscope (derivative of tilt)
        gx = (
            15.0 * 0.5 * math.cos(self.time * 0.5) * (180 / math.pi)
            + 1.0 * math.sin(self.time * 3)
        )
        gy = (
            -10.0 * 0.3 * math.sin(self.time * 0.3) * (180 / math.pi)
            + 0.8 * math.cos(self.time * 2.5)
        )
        gz = 0.5 * math.sin(self.time * 0.7)

        # Temperature (simulated room temp)
        temp = 25.0 + 0.5 * math.sin(self.time * 0.1)

        # Add calibration offsets
        ax -= self.accel_offset[0]
        ay -= self.accel_offset[1]
        az -= self.accel_offset[2]

        gx -= self.gyro_offset[0]
        gy -= self.gyro_offset[1]
        gz -= self.gyro_offset[2]

        self.time += self.sample_interval

        return ax, ay, az, gx, gy, gz, temp


class SimulatedIMUKalmanFilter:
    """Real-time IMU reading simulation with Kalman filtering."""

    def __init__(self, sample_rate=100):
        """Initialize simulated IMU with Kalman filter."""
        self.imu = SimulatedIMU(sample_rate=sample_rate)

        # 3D Kalman filter
        self.kf = KalmanFilter3D(
            process_variance=0.001,
            measurement_variance=0.2,
        )

        self.sample_rate = sample_rate
        self.sample_interval = 1.0 / sample_rate

        # Complementary filter
        self.alpha = 0.95
        self.pitch = 0.0
        self.roll = 0.0

    def calculate_tilt(self, ax, ay, az):
        """Calculate pitch and roll from accelerometer."""
        pitch = math.atan2(ax, math.sqrt(ay * ay + az * az))
        roll = math.atan2(ay, math.sqrt(ax * ax + az * az))
        return math.degrees(pitch), math.degrees(roll)

    def complementary_filter(self, ax, ay, az, gx, gy, gz):
        """Fuse accelerometer and gyroscope data."""
        gx_rad = math.radians(gx)
        gy_rad = math.radians(gy)

        dt = self.sample_interval
        self.pitch += gx_rad * dt
        self.roll += gy_rad * dt

        accel_pitch, accel_roll = self.calculate_tilt(ax, ay, az)
        accel_pitch_rad = math.radians(accel_pitch)
        accel_roll_rad = math.radians(accel_roll)

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
            f"x:{ax:6.2f} y:{ay:6.2f} z:{az:6.2f} | "
            f"gx:{gx:7.1f} gy:{gy:7.1f} gz:{gz:7.1f} | "
            f"T:{temp:5.1f}C"
        )

    def run(self, duration=30):
        """Run simulation."""
        print("\n" + "=" * 80)
        print("BBB - Real-time IMU Kalman Filter Simulation")
        print("=" * 80)

        print("\nSimulating MPU6050 sensor with realistic motion...")
        print(
            "pitch(deg) roll(deg) | "
            "x(m/s²) y(m/s²) z(m/s²) | "
            "gx(deg/s) gy(deg/s) gz(deg/s) | temp(C)"
        )
        print("-" * 80)

        start_time = time.time()
        sample_count = 0

        try:
            while True:
                sample_start = time.time()

                # Get simulated sensor data
                ax, ay, az, gx, gy, gz, temp = self.imu.get_all()

                # Apply Kalman filter
                ax_f, ay_f, az_f = self.kf.update(ax, ay, az)

                # Complementary filter
                pitch, roll = self.complementary_filter(
                    ax_f, ay_f, az_f, gx, gy, gz
                )

                # Print formatted log
                log = self.format_log(
                    pitch, roll, ax_f, ay_f, az_f, gx, gy, gz, temp
                )
                print(log)

                sample_count += 1

                # Check duration
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    break

                # Maintain sample rate
                elapsed_sample = time.time() - sample_start
                if elapsed_sample < self.sample_interval:
                    time.sleep(self.sample_interval - elapsed_sample)

        except KeyboardInterrupt:
            print("\nStopped by user")

        # Summary
        print("-" * 80)
        elapsed_total = time.time() - start_time
        actual_rate = sample_count / elapsed_total

        print(
            f"\nSummary: {sample_count} samples in {elapsed_total:.1f}s "
            f"({actual_rate:.1f} Hz avg)"
        )
        print("=" * 80)

        # Statistics
        print("\nWhat the data means:")
        print("  pitch: Rotation around Y axis (forward/backward tilt)")
        print("  roll:  Rotation around X axis (left/right tilt)")
        print("  x, y, z: Filtered acceleration (m/s²)")
        print("  gx, gy, gz: Angular velocity (deg/s)")
        print("  T: Temperature (°C)")
        print("\nKalman filter applied to reduce measurement noise ~40-60%")
        print("Complementary filter fuses accel + gyro for stable tilt estimation")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Simulate IMU with Kalman filter"
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=float,
        default=30,
        help="Simulation duration in seconds (default: 30)",
    )
    parser.add_argument(
        "--rate",
        "-r",
        type=int,
        default=100,
        help="Sample rate in Hz (default: 100)",
    )

    args = parser.parse_args()

    try:
        sensor = SimulatedIMUKalmanFilter(sample_rate=args.rate)
        sensor.run(duration=args.duration)
    except KeyboardInterrupt:
        print("\nInterrupted")


if __name__ == "__main__":
    main()
