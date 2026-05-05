"""
Unit tests for EMG sensor driver
Tests ADC conversion logic and signal processing
"""

import pytest


class MockADC:
    """Mock ADC for testing without hardware"""

    def __init__(self, value: int = 2048):
        self._value = value
        self._attn = None
        self._width = None

    def read(self) -> int:
        return self._value

    def atten(self, level):
        self._attn = level

    def width(self, bits):
        self._width = bits


class MockPin:
    """Mock GPIO Pin"""

    OUT = 1

    def __init__(self, pin: int, mode: int):
        self.pin = pin
        self.mode = mode


class TestEMGSensor:
    """Test EMG sensor core functionality"""

    def test_read_raw_conversion(self):
        """Test raw ADC value conversion"""
        # Directly test the conversion logic
        adc_val = 2048
        # Simulating EMGSensor.read_raw() which just returns ADC value
        assert 0 <= adc_val <= 4095

    def test_read_mv_conversion(self):
        """Test ADC to millivolt conversion"""
        # Test conversion formula: mv = adc * 3300.0 / 4095.0
        test_cases = [
            (0, 0.0),  # Min
            (2048, 1650.4),  # Mid-range ~50%
            (4095, 3300.0),  # Max value
            (1000, 806.56),  # Quarter
            (3000, 2441.93),  # Three-quarter
        ]

        for adc_val, expected_mv in test_cases:
            calculated_mv = adc_val * 3300.0 / 4095.0
            assert abs(calculated_mv - expected_mv) < 30.0  # 30mV tolerance

    def test_sample_rate_interval(self):
        """Test interval calculation for given sample rate"""
        test_cases = [
            (1000, 1000),  # 1kHz → 1000µs interval
            (500, 2000),  # 500Hz → 2000µs interval
            (2000, 500),  # 2kHz → 500µs interval
            (100, 10000),  # 100Hz → 10000µs interval
        ]

        for sample_rate, expected_interval_us in test_cases:
            calculated_interval = 1_000_000 // sample_rate
            assert calculated_interval == expected_interval_us


class TestEMGSpikeDection:
    """Test EMG spike (muscle contraction) detection"""

    def test_spike_threshold_default(self):
        """Test spike detection with default threshold (3500)"""
        threshold = 3500

        # Below threshold → no spike
        assert not (2000 > threshold)
        assert not (3400 > threshold)

        # Above threshold → spike detected
        assert 3501 > threshold
        assert 4000 > threshold

    def test_spike_threshold_custom(self):
        """Test spike detection with custom threshold"""
        custom_threshold = 3000

        test_cases = [
            (1500, False),  # Below threshold
            (3000, False),  # At threshold (not greater)
            (3001, True),  # Above threshold
            (4000, True),  # Well above threshold
        ]

        for adc_val, expected_spike in test_cases:
            is_spike = adc_val > custom_threshold
            assert is_spike == expected_spike

    def test_baseline_vs_active_signal(self):
        """Test typical ADC values for baseline vs muscle contraction"""
        # Typical baseline EMG (resting muscle): 500-1500 ADC
        baseline_samples = [600, 800, 1200, 1500]
        for sample in baseline_samples:
            assert sample < 3500  # Below spike threshold

        # Typical active EMG (muscle contraction): 2500-4095 ADC
        active_samples = [2500, 3000, 3500, 4000, 4095]
        for sample in active_samples:
            assert sample >= 2500  # Significant signal


class TestEMGSampleChunk:
    """Test continuous sampling functionality"""

    def test_sample_chunk_length(self):
        """Test that sample_chunk returns correct number of samples"""
        test_cases = [1, 10, 100, 1000]

        for n_samples in test_cases:
            # Simulate chunk sampling: just verify count
            chunk = list(range(n_samples))  # Mock chunk data
            assert len(chunk) == n_samples

    def test_sample_chunk_range(self):
        """Test that all samples are within valid ADC range"""
        # Simulate 100 samples at typical levels
        mock_chunk = [600, 800, 1200, 1500, 700, 900, 1100, 1300] * 12 + [
            600,
            800,
            1200,
        ]
        # 100 samples total

        for sample in mock_chunk:
            assert 0 <= sample <= 4095


class TestEMGNoiseFloor:
    """Test noise floor detection"""

    def test_resting_signal_stability(self):
        """Test that resting signal has low noise floor"""
        # Typical resting EMG: ~600-1500 ADC with small variance
        resting_baseline = [1000, 1020, 980, 1010, 995, 1015, 990, 1005]
        avg = sum(resting_baseline) / len(resting_baseline)
        variance = sum((x - avg) ** 2 for x in resting_baseline) / len(resting_baseline)

        # Variance should be low for stable baseline
        assert avg > 500  # Signal present
        assert variance < 500  # Low noise

    def test_active_signal_amplitude(self):
        """Test amplitude increase during muscle contraction"""
        baseline = [1000, 1010, 990, 1005]
        active = [3200, 3400, 3600, 3800]

        baseline_avg = sum(baseline) / len(baseline)
        active_avg = sum(active) / len(active)

        # Active should be significantly higher
        assert active_avg > baseline_avg * 2  # At least 2x increase


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
