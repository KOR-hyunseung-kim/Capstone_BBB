"""
Kalman Filter for Accelerometer Noise Reduction in BBB Safety Mode
- Estimates true acceleration from noisy sensor readings
- MicroPython compatible (no numpy dependency)
- Supports 1D, 2D, 3D filtering via stacking single filters
"""

import math


class KalmanFilter1D:
    """
    1D Kalman Filter for single-axis acceleration filtering.
    Estimates position and velocity from accelerometer measurements.
    """

    def __init__(
        self,
        process_variance: float = 0.01,
        measurement_variance: float = 0.1,
        initial_value: float = 0.0,
        initial_estimate_error: float = 1.0,
    ):
        """
        Initialize 1D Kalman Filter.

        Args:
            process_variance: Process noise (Q) - models unpredictable changes
            measurement_variance: Measurement noise (R) - sensor noise level
            initial_value: Initial state estimate (m/s²)
            initial_estimate_error: Initial estimate error (P)
        """
        self.q = process_variance
        self.r = measurement_variance
        self.x = initial_value
        self.p = initial_estimate_error
        self.k = 0.0

    def update(self, measurement: float) -> float:
        """
        Update filter with new measurement and return filtered estimate.

        Args:
            measurement: Raw accelerometer reading (m/s²)

        Returns:
            Filtered acceleration estimate (m/s²)
        """
        self.p = self.p + self.q
        self.k = self.p / (self.p + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1 - self.k) * self.p

        return self.x

    def reset(self, initial_value: float = 0.0) -> None:
        """Reset filter state."""
        self.x = initial_value
        self.p = 1.0
        self.k = 0.0


class KalmanFilter3D:
    """
    3D Kalman Filter for accelerometer (ax, ay, az filtering).
    Uses three independent 1D filters for each axis.
    """

    def __init__(
        self,
        process_variance: float = 0.01,
        measurement_variance: float = 0.1,
    ):
        """
        Initialize 3D Kalman Filter (one filter per axis).

        Args:
            process_variance: Process noise (Q)
            measurement_variance: Measurement noise (R)
        """
        self.filter_x = KalmanFilter1D(process_variance, measurement_variance)
        self.filter_y = KalmanFilter1D(process_variance, measurement_variance)
        self.filter_z = KalmanFilter1D(process_variance, measurement_variance)

    def update(self, ax: float, ay: float, az: float) -> tuple:
        """
        Update filter with 3-axis measurement.

        Args:
            ax: X-axis acceleration (m/s²)
            ay: Y-axis acceleration (m/s²)
            az: Z-axis acceleration (m/s²)

        Returns:
            Tuple of (filtered_ax, filtered_ay, filtered_az)
        """
        return (
            self.filter_x.update(ax),
            self.filter_y.update(ay),
            self.filter_z.update(az),
        )

    def reset(self) -> None:
        """Reset all axis filters."""
        self.filter_x.reset()
        self.filter_y.reset()
        self.filter_z.reset()


class AdaptiveKalmanFilter1D:
    """
    Adaptive Kalman Filter that adjusts measurement variance based on
    detected signal variations (handles changing noise levels).
    """

    def __init__(
        self,
        process_variance: float = 0.01,
        base_measurement_variance: float = 0.1,
        adaptation_rate: float = 0.01,
    ):
        """
        Initialize Adaptive 1D Kalman Filter.

        Args:
            process_variance: Process noise (Q)
            base_measurement_variance: Base measurement noise (R)
            adaptation_rate: How fast to adapt to changing noise
        """
        self.q = process_variance
        self.r_base = base_measurement_variance
        self.r = base_measurement_variance
        self.x = 0.0
        self.p = 1.0
        self.k = 0.0
        self.adaptation_rate = adaptation_rate
        self.residuals = []
        self.max_residuals = 50

    def update(self, measurement: float) -> float:
        """
        Update with adaptive measurement variance.

        Args:
            measurement: Raw sensor reading

        Returns:
            Filtered estimate
        """
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
