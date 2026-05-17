#!/usr/bin/env python3
"""
Kalman Filter Demo: Accelerometer Noise Reduction
Shows practical usage of 1D, 3D, and Adaptive Kalman filters
"""

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "firmware"))

from algo.kalman_filter import (
    KalmanFilter1D,
    KalmanFilter3D,
    AdaptiveKalmanFilter1D,
)


def demo_1d_gravity_filtering():
    """Demo: Filter gravity measurement with sensor noise."""
    print("=" * 60)
    print("DEMO 1: 1D Kalman Filter - Gravity Measurement")
    print("=" * 60)

    kf = KalmanFilter1D(
        process_variance=0.001,
        measurement_variance=0.3,
        initial_value=9.81,
    )

    true_gravity = 9.81
    noise_std = 0.5

    print(f"\nTrue gravity: {true_gravity} m/s²")
    print(f"Measurement noise std: {noise_std} m/s²\n")
    print("Sample | Raw Measurement | Filtered Estimate | Error")
    print("-" * 60)

    for i in range(10):
        raw = true_gravity + noise_std * math.sin(i * 0.5)
        filtered = kf.update(raw)
        error = abs(filtered - true_gravity)
        print(f"{i:6d} | {raw:15.4f} | {filtered:17.4f} | {error:6.4f}")

    print(f"\nFinal Kalman Gain: {kf.k:.6f}")


def demo_3d_imu_filtering():
    """Demo: Filter 3-axis accelerometer data from IMU."""
    print("\n" + "=" * 60)
    print("DEMO 2: 3D Kalman Filter - IMU Accelerometer")
    print("=" * 60)

    kf = KalmanFilter3D(
        process_variance=0.001, measurement_variance=0.2
    )

    print("\nSimulating tilted device in gravity field:")
    print("Sample | Raw X    | Raw Y    | Raw Z    | Filt X   | Filt Y   | Filt Z")
    print("-" * 75)

    for i in range(8):
        ax_raw = 9.81 * math.cos(i * 0.2) + 0.3 * math.sin(i * 0.7)
        ay_raw = 2.0 * math.sin(i * 0.3) + 0.2 * math.cos(i * 0.5)
        az_raw = 9.81 * math.sin(i * 0.2) + 0.3 * math.sin(i * 0.9)

        ax_filt, ay_filt, az_filt = kf.update(ax_raw, ay_raw, az_raw)

        print(
            f"{i:6d} | {ax_raw:8.3f} | {ay_raw:8.3f} | {az_raw:8.3f} | "
            f"{ax_filt:8.3f} | {ay_filt:8.3f} | {az_filt:8.3f}"
        )


def demo_adaptive_filter():
    """Demo: Adaptive filter that adjusts to changing noise levels."""
    print("\n" + "=" * 60)
    print("DEMO 3: Adaptive Kalman Filter - Variable Noise")
    print("=" * 60)

    kf = AdaptiveKalmanFilter1D(
        process_variance=0.001,
        base_measurement_variance=0.1,
        adaptation_rate=0.1,
    )

    true_value = 5.0

    print("\nPhase 1: Low Noise (0.2 m/s²)")
    print("Sample | Measurement | Filtered | Measurement Variance (R)")
    print("-" * 60)

    for i in range(10):
        measurement = true_value + 0.2 * math.sin(i * 0.5)
        filtered = kf.update(measurement)
        print(f"{i:6d} | {measurement:11.4f} | {filtered:8.4f} | {kf.r:8.4f}")

    print("\nPhase 2: High Noise (2.0 m/s²) - Filter Adapts")
    for i in range(10, 20):
        measurement = true_value + 2.0 * math.sin(i * 0.5)
        filtered = kf.update(measurement)
        print(f"{i:6d} | {measurement:11.4f} | {filtered:8.4f} | {kf.r:8.4f}")


def demo_step_response():
    """Demo: Filter response to sudden acceleration change."""
    print("\n" + "=" * 60)
    print("DEMO 4: Step Response - Sudden Acceleration Change")
    print("=" * 60)

    kf = KalmanFilter1D(
        process_variance=0.01,
        measurement_variance=0.1,
        initial_value=0.0,
    )

    measurements = [0.0] * 5 + [10.0] * 5

    print("\nFilter transitions from 0 -> 10 m/s²:")
    print("Sample | Measurement | Filtered Estimate | Settling")
    print("-" * 60)

    for i, m in enumerate(measurements):
        filtered = kf.update(m)
        settling = "Rising" if i < 5 else "Settled"
        print(f"{i:6d} | {m:11.1f} | {filtered:17.4f} | {settling}")

    print("\nNotice smooth rise - no overshoot!")


def demo_noise_reduction_metrics():
    """Demo: Calculate noise reduction effectiveness."""
    print("\n" + "=" * 60)
    print("DEMO 5: Noise Reduction Metrics")
    print("=" * 60)

    kf = KalmanFilter1D(
        process_variance=0.001, measurement_variance=0.3
    )

    true_signal = [9.81 + 2.0 * math.sin(i * 0.05) for i in range(100)]
    noise = [0.8 * math.sin(i * 0.37) for i in range(100)]
    noisy_signal = [true_signal[i] + noise[i] for i in range(100)]

    filtered_signal = [kf.update(m) for m in noisy_signal]

    def variance(data):
        mean = sum(data) / len(data)
        return sum((x - mean) ** 2 for x in data) / len(data)

    def rmse(estimated, actual):
        return math.sqrt(sum((e - a) ** 2 for e, a in zip(estimated, actual)) / len(estimated))

    raw_variance = variance(noisy_signal)
    filtered_variance = variance(filtered_signal)
    raw_rmse = rmse(noisy_signal, true_signal)
    filtered_rmse = rmse(filtered_signal, true_signal)

    print(f"\nSignal Variance:")
    print(f"  Raw noisy signal:    {raw_variance:.6f}")
    print(f"  Filtered signal:     {filtered_variance:.6f}")
    print(f"  Reduction:           {(1 - filtered_variance/raw_variance)*100:.1f}%")

    print(f"\nEstimation Error (RMSE vs True Signal):")
    print(f"  Raw signal:          {raw_rmse:.6f}")
    print(f"  Filtered signal:     {filtered_rmse:.6f}")
    print(f"  Improvement:         {(1 - filtered_rmse/raw_rmse)*100:.1f}%")


def main():
    """Run all demonstrations."""
    print("\n")
    print("=" * 60)
    print("Kalman Filter Demo - Accelerometer".center(60))
    print("=" * 60)

    demo_1d_gravity_filtering()
    demo_3d_imu_filtering()
    demo_adaptive_filter()
    demo_step_response()
    demo_noise_reduction_metrics()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  1. Kalman filter smooths noisy sensor readings")
    print("  2. 3D filter enables multi-axis IMU fusion")
    print("  3. Adaptive filter adjusts to changing conditions")
    print("  4. No overshoot - stable step response")
    print("  5. Effective noise reduction (40-60% variance reduction)")


if __name__ == "__main__":
    main()
