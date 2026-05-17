"""
Unit and integration tests for EMG fatigue detection algorithm
Tests RMS calculation, calibration, and fatigue level judgment
"""

import pytest
import math
import sys
from pathlib import Path

# Add firmware directory to path for imports
firmware_path = Path(__file__).parent.parent / "firmware"
sys.path.insert(0, str(firmware_path))


class MockEMGSensor:
    """Mock EMGSensor for testing without hardware"""

    def __init__(self, test_data_sequence=None):
        """
        Initialize mock sensor

        Args:
            test_data_sequence: List of lists, each inner list is samples for one chunk.
                               If None, defaults to [[2000] * 1000]. Pass [] for empty sequence.
        """
        if test_data_sequence is None:
            self.test_data_sequence = [[2000] * 1000]
        else:
            self.test_data_sequence = test_data_sequence
        self.sequence_index = 0

    def sample_chunk(self, n_samples):
        """Return predefined test data"""
        if self.sequence_index < len(self.test_data_sequence):
            data = self.test_data_sequence[self.sequence_index]
            self.sequence_index += 1
            return data[: n_samples]  # Trim to requested size
        return []  # Return empty when sequence exhausted


class MockVibratorMotor:
    """Mock VibratorMotor for testing without hardware"""

    def __init__(self, gpio_pin=None, frequency=100):
        self.alert_history = []

    def alert_pattern(self, level):
        """Record alert for verification"""
        self.alert_history.append(level)

    def stop(self):
        """No-op for mock"""
        pass


# ============================================================================
# Test: RMS Calculation
# ============================================================================


def test_rms_constant_signal():
    """Test RMS of constant signal"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    # Constant signal of 100
    samples = [100] * 1000
    rms = processor._calculate_rms(samples)

    assert rms == pytest.approx(100.0, rel=1e-5)


def test_rms_varying_signal():
    """Test RMS of varying signal"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    # Signal varying between 1000 and 3000
    samples = [1000, 2000, 3000, 2000, 1000] * 200
    rms = processor._calculate_rms(samples)

    # RMS should be higher than mean but captures variance
    mean = sum(samples) / len(samples)
    assert rms > 0
    assert rms >= mean


def test_rms_zero():
    """Test RMS of empty or zero samples"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    assert processor._calculate_rms([]) == 0.0
    assert processor._calculate_rms([0] * 100) == 0.0


# ============================================================================
# Test: Calibration
# ============================================================================


def test_calibration_single_chunk():
    """Test calibration with single chunk of stable signal"""
    from algo.emg_processor import EMGProcessor

    # Baseline: constant signal of 1500
    baseline_data = [[1500] * 1000]
    mock_sensor = MockEMGSensor(baseline_data)
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor, chunk_size=1000)

    success = processor.calibrate(duration_sec=1)

    assert success
    assert processor.baseline_rms == pytest.approx(1500.0, rel=1e-5)
    assert processor.current_mode == "monitoring"


def test_calibration_multiple_chunks():
    """Test calibration over multiple chunks"""
    from algo.emg_processor import EMGProcessor

    # Baseline: 3 seconds of constant 2000
    baseline_data = [[2000] * 1000 for _ in range(3)]
    mock_sensor = MockEMGSensor(baseline_data)
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor, chunk_size=1000)

    success = processor.calibrate(duration_sec=3)

    assert success
    assert processor.baseline_rms == pytest.approx(2000.0, rel=1e-5)
    assert len(processor.baseline_samples) == 3000


def test_calibration_no_data():
    """Test calibration failure when no data available"""
    from algo.emg_processor import EMGProcessor

    # Empty sensor
    mock_sensor = MockEMGSensor([])
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    success = processor.calibrate(duration_sec=1)

    assert not success
    assert processor.baseline_rms is None


# ============================================================================
# Test: Fatigue Level Detection
# ============================================================================


def test_fatigue_normal():
    """Test normal fatigue level (>= 90% baseline)"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    # Set baseline manually
    processor.baseline_rms = 2000.0

    # Test at 92% of baseline
    level, fatigue_pct = processor.get_fatigue_level(rms=1840)

    assert level == "normal"
    assert fatigue_pct == pytest.approx(92.0, rel=0.1)


def test_fatigue_warning():
    """Test warning fatigue level (70-90% baseline)"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    processor.baseline_rms = 2000.0

    # Test at 80% of baseline (between 70 and 90)
    level, fatigue_pct = processor.get_fatigue_level(rms=1600)

    assert level == "warning"
    assert fatigue_pct == pytest.approx(80.0, rel=0.1)


def test_fatigue_critical():
    """Test critical fatigue level (< 60% baseline)"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    processor.baseline_rms = 2000.0

    # Test at 50% of baseline
    level, fatigue_pct = processor.get_fatigue_level(rms=1000)

    assert level == "critical"
    assert fatigue_pct == pytest.approx(50.0, rel=0.1)


def test_fatigue_no_baseline():
    """Test fatigue detection without baseline (should default to normal)"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    # No calibration
    level, fatigue_pct = processor.get_fatigue_level(rms=1000)

    assert level == "normal"
    assert fatigue_pct == 100.0


# ============================================================================
# Test: Haptic Feedback Triggering
# ============================================================================


def test_alert_on_warning_transition():
    """Test that alert is triggered when transitioning to warning"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    processor.baseline_rms = 2000.0

    # First call: normal level at 92% (should not alert)
    processor.update_with_feedback(rms=1840)
    assert len(mock_motor.alert_history) == 0

    # Second call: drop to warning at 80% (should alert)
    processor.update_with_feedback(rms=1600)
    assert len(mock_motor.alert_history) == 1
    assert mock_motor.alert_history[0] == "warning"


def test_alert_on_critical_transition():
    """Test that alert is triggered when transitioning to critical"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    processor.baseline_rms = 2000.0

    # Transition: normal → critical (skip warning)
    processor.update_with_feedback(rms=1850)  # normal (92.5%)
    processor.update_with_feedback(rms=1200)  # critical (60%)
    assert len(mock_motor.alert_history) == 1
    assert mock_motor.alert_history[0] == "critical"


def test_no_alert_on_stable_level():
    """Test that alert is not triggered if level doesn't change"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor()
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    processor.baseline_rms = 2000.0

    # First call to establish baseline level (normal)
    processor.update_with_feedback(rms=1850)  # normal (92.5%)
    initial_alerts = len(mock_motor.alert_history)

    # Multiple calls at same level (should not trigger new alerts)
    for rms in [1860, 1840, 1850]:  # all normal (92-93%)
        processor.update_with_feedback(rms)

    assert len(mock_motor.alert_history) == initial_alerts


# ============================================================================
# Test: Integration (Calibration + Monitoring)
# ============================================================================


def test_full_calibration_and_monitoring():
    """Integration test: calibration followed by monitoring cycle"""
    from algo.emg_processor import EMGProcessor

    # Baseline: 1 second at 2000, then drop to 1000
    test_sequence = [
        [2000] * 1000,  # Calibration chunk
        [1000] * 1000,  # Monitoring chunk (50% = critical)
    ]
    mock_sensor = MockEMGSensor(test_sequence)
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    # Calibrate
    assert processor.calibrate(duration_sec=1)
    assert processor.baseline_rms == pytest.approx(2000.0)

    # Monitor
    rms, level = processor.run_monitoring_cycle()
    assert rms == pytest.approx(1000.0)
    assert level == "critical"
    assert len(mock_motor.alert_history) == 1


def test_safety_mode_controller_integration():
    """Integration test for SafetyModeController"""
    from algo.emg_processor import EMGProcessor, SafetyModeController

    test_sequence = [[2000] * 1000]
    mock_sensor = MockEMGSensor(test_sequence)
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)
    controller = SafetyModeController(processor)

    # Start safety mode
    success = controller.start(duration_sec=1)
    assert success
    assert controller.running

    # Cleanup
    controller.stop()
    assert not controller.running


# ============================================================================
# Test: Reset and State Management
# ============================================================================


def test_processor_reset():
    """Test reset clears calibration and state"""
    from algo.emg_processor import EMGProcessor

    mock_sensor = MockEMGSensor([[2000] * 1000])
    mock_motor = MockVibratorMotor()
    processor = EMGProcessor(mock_sensor, mock_motor)

    # Calibrate
    processor.calibrate(duration_sec=1)
    assert processor.baseline_rms is not None

    # Reset
    processor.reset()
    assert processor.baseline_rms is None
    assert processor.current_mode == "idle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
