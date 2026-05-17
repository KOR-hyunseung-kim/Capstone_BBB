"""
Pytest suite for Kalman Filter accelerometer filtering.
Tests noise reduction, convergence, and stability.
"""

import math
import pytest
import sys
from pathlib import Path

firmware_path = Path(__file__).parent.parent / "firmware"
sys.path.insert(0, str(firmware_path))

from algo.kalman_filter import (
    KalmanFilter1D,
    KalmanFilter3D,
    AdaptiveKalmanFilter1D,
)


class TestKalmanFilter1D:
    """Test 1D Kalman Filter for single-axis acceleration."""

    def test_initialization(self):
        """Filter initializes with correct parameters."""
        kf = KalmanFilter1D(
            process_variance=0.01,
            measurement_variance=0.1,
            initial_value=5.0,
        )
        assert kf.x == 5.0
        assert kf.p == 1.0
        assert kf.q == 0.01
        assert kf.r == 0.1

    def test_constant_value_convergence(self):
        """Filter converges to constant input value."""
        kf = KalmanFilter1D(
            process_variance=0.001, measurement_variance=1.0
        )
        true_value = 9.81
        measurements = [true_value + 0.5 * math.sin(i * 0.1) for i in range(100)]

        estimates = [kf.update(m) for m in measurements]

        assert abs(estimates[-1] - true_value) < 0.2
        assert abs(estimates[-1] - true_value) < abs(estimates[0] - true_value)

    def test_noise_reduction(self):
        """Filter reduces random measurement noise."""
        kf = KalmanFilter1D(process_variance=0.001, measurement_variance=0.5)
        true_value = 5.0
        noise_std = 2.0
        measurements = [
            true_value + noise_std * math.sin(i) for i in range(200)
        ]

        estimates = [kf.update(m) for m in measurements]

        estimate_variance = self._calculate_variance(estimates[-50:])
        measurement_variance = self._calculate_variance(measurements[-50:])

        assert estimate_variance < measurement_variance
        assert estimate_variance < noise_std * noise_std

    def test_step_response(self):
        """Filter responds to step change in input."""
        kf = KalmanFilter1D(
            process_variance=0.01, measurement_variance=0.1
        )
        measurements = [0.0] * 50 + [10.0] * 50

        estimates = [kf.update(m) for m in measurements]

        assert estimates[49] < 5.0
        assert estimates[99] > 8.0
        assert abs(estimates[99] - 10.0) < 1.0

    def test_reset(self):
        """Filter resets to initial state."""
        kf = KalmanFilter1D(initial_value=0.0)
        kf.update(5.0)
        kf.update(5.0)
        assert kf.x != 0.0

        kf.reset(0.0)
        assert kf.x == 0.0
        assert kf.p == 1.0

    def test_gain_converges(self):
        """Kalman gain stabilizes as filter converges."""
        kf = KalmanFilter1D(
            process_variance=0.001, measurement_variance=0.1
        )
        measurements = [5.0] * 100

        gains = []
        for m in measurements:
            kf.update(m)
            gains.append(kf.k)

        assert gains[0] > gains[-1]
        assert abs(gains[-1] - gains[-2]) < 0.0001

    @staticmethod
    def _calculate_variance(values):
        """Calculate sample variance."""
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)


class TestKalmanFilter3D:
    """Test 3D Kalman Filter for multi-axis acceleration."""

    def test_initialization(self):
        """3D filter initializes three independent filters."""
        kf = KalmanFilter3D(
            process_variance=0.01, measurement_variance=0.1
        )
        assert kf.filter_x is not None
        assert kf.filter_y is not None
        assert kf.filter_z is not None

    def test_three_axis_filtering(self):
        """Filter processes all three axes independently."""
        kf = KalmanFilter3D(
            process_variance=0.001, measurement_variance=0.5
        )

        measurements = [
            (9.81 + 0.2 * math.sin(i * 0.1), 0.1 * math.cos(i * 0.1), -0.3)
            for i in range(100)
        ]

        estimates = [kf.update(ax, ay, az) for ax, ay, az in measurements]

        ax_est, ay_est, az_est = estimates[-1]
        assert abs(ax_est - 9.81) < 0.3
        assert abs(ay_est - 0.0) < 0.3
        assert abs(az_est - (-0.3)) < 0.3

    def test_axis_independence(self):
        """Each axis filters independently without cross-coupling."""
        kf = KalmanFilter3D(
            process_variance=0.001, measurement_variance=0.1
        )

        high_noise_x = [5.0 + 5.0 * math.sin(i * 0.5) for i in range(100)]
        low_noise_y = [0.0] * 100
        low_noise_z = [0.0] * 100

        estimates = [
            kf.update(high_noise_x[i], low_noise_y[i], low_noise_z[i])
            for i in range(100)
        ]

        _, y_final, z_final = estimates[-1]
        assert abs(y_final) < 0.1
        assert abs(z_final) < 0.1

    def test_reset_all_axes(self):
        """Reset clears all three filters."""
        kf = KalmanFilter3D()
        kf.update(5.0, 3.0, 2.0)
        kf.reset()

        assert kf.filter_x.x == 0.0
        assert kf.filter_y.x == 0.0
        assert kf.filter_z.x == 0.0


class TestAdaptiveKalmanFilter1D:
    """Test Adaptive Kalman Filter that adjusts to changing noise."""

    def test_initialization(self):
        """Adaptive filter initializes correctly."""
        kf = AdaptiveKalmanFilter1D(
            process_variance=0.01,
            base_measurement_variance=0.1,
            adaptation_rate=0.05,
        )
        assert kf.r == 0.1
        assert kf.adaptation_rate == 0.05

    def test_adapts_to_increasing_noise(self):
        """Filter increases measurement variance with higher noise."""
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

        assert r_high_noise > r_low_noise

    def test_adapts_to_decreasing_noise(self):
        """Filter decreases measurement variance with lower noise."""
        kf = AdaptiveKalmanFilter1D(
            process_variance=0.001,
            base_measurement_variance=1.0,
            adaptation_rate=0.1,
        )

        high_noise_meas = [5.0 + 2.0 * math.sin(i) for i in range(50)]
        low_noise_meas = [5.0 + 0.1 * math.sin(i) for i in range(50)]

        for m in high_noise_meas:
            kf.update(m)

        r_high_noise = kf.r

        for m in low_noise_meas:
            kf.update(m)

        r_low_noise = kf.r

        assert r_low_noise < r_high_noise

    def test_residual_tracking(self):
        """Filter tracks recent residuals for adaptation."""
        kf = AdaptiveKalmanFilter1D(
            process_variance=0.001,
            base_measurement_variance=0.1,
            adaptation_rate=0.1,
        )

        measurements = [5.0 + 0.5 * math.sin(i) for i in range(100)]
        for m in measurements:
            kf.update(m)

        assert len(kf.residuals) <= kf.max_residuals
        assert len(kf.residuals) > 0


class TestAccelerometerSignalProcessing:
    """Integration tests with realistic accelerometer signals."""

    def test_gravity_measurement_filtering(self):
        """Filter refines noisy gravity measurement."""
        kf = KalmanFilter1D(
            process_variance=0.001, measurement_variance=0.2
        )

        true_gravity = 9.81
        noise_std = 0.5
        measurements = [
            true_gravity + noise_std * math.sin(i * 0.05) for i in range(200)
        ]

        estimates = [kf.update(m) for m in measurements]

        assert abs(estimates[-1] - true_gravity) < 0.2

    def test_dynamic_acceleration_tracking(self):
        """Filter follows dynamic acceleration changes."""
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

        assert estimates[29] < 2.0
        assert estimates[59] > 8.0
        assert estimates[79] > 6.0

    def test_imu_gyroscope_stabilization(self):
        """Filter smooths high-frequency noise from drifting signal."""
        kf = KalmanFilter1D(
            process_variance=0.001, measurement_variance=0.5
        )

        drift_signal = [
            0.5 + 0.01 * i + 0.5 * math.sin(i * 0.2) for i in range(100)
        ]

        estimates = [kf.update(m) for m in drift_signal]

        def signal_smoothness(data):
            diffs = [abs(data[i + 1] - data[i]) for i in range(len(data) - 1)]
            return sum(diffs) / len(diffs)

        raw_smoothness = signal_smoothness(drift_signal)
        filtered_smoothness = signal_smoothness(estimates)

        assert filtered_smoothness < raw_smoothness


@pytest.fixture
def sample_accelerometer_data():
    """Generate synthetic accelerometer data with noise."""
    true_signal = [
        9.81 + 2.0 * math.sin(i * 0.05) for i in range(200)
    ]
    noise = [0.8 * math.sin(i * 0.37) for i in range(200)]
    return [true_signal[i] + noise[i] for i in range(200)]


def test_filter_vs_raw_data(sample_accelerometer_data):
    """Filtered signal has lower variance than raw data."""
    kf = KalmanFilter1D(
        process_variance=0.001, measurement_variance=0.3
    )

    filtered = [kf.update(m) for m in sample_accelerometer_data]

    def variance(data):
        mean = sum(data) / len(data)
        return sum((x - mean) ** 2 for x in data) / len(data)

    raw_var = variance(sample_accelerometer_data)
    filtered_var = variance(filtered)

    assert filtered_var < raw_var
    assert (raw_var - filtered_var) / raw_var > 0.3
