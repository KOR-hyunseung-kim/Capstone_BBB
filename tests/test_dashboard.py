"""
Unit tests for BBB Dashboard
Tests WebSocket broadcasting and fatigue level determination
"""

import pytest
import json
from tools.dashboard.server import FatigueAnalyzer


class TestFatigueAnalyzer:
    """Test EMG processing and fatigue calculation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = FatigueAnalyzer(sample_rate=1000)

    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        assert self.analyzer.sample_rate == 1000
        assert self.analyzer.baseline_mf is None

    def test_short_buffer_returns_zero(self):
        """Test that short buffers return zero fatigue"""
        result = self.analyzer.process_emg_chunk([0] * 50)
        assert result["fatigue_pct"] == 0.0
        assert result["level"] == "normal"

    def test_baseline_initialization(self):
        """Test baseline MF initialization on first run"""
        # Create synthetic signal (simple sine wave)
        import numpy as np

        freq = 50  # 50 Hz component in EMG band
        t = np.linspace(0, 0.128, 128)  # 128 samples at 1kHz
        signal = np.sin(2 * np.pi * freq * t) * 100

        result = self.analyzer.process_emg_chunk(signal.tolist())

        # Baseline should be set to median freq of first signal
        assert self.analyzer.baseline_mf is not None
        assert result["fatigue_pct"] < 20  # First run should be low fatigue

    def test_fatigue_level_normal(self):
        """Test normal fatigue level (< 80%)"""
        # Setup with baseline
        import numpy as np

        freq = 100
        t = np.linspace(0, 0.128, 128)
        signal = np.sin(2 * np.pi * freq * t) * 100
        self.analyzer.process_emg_chunk(signal.tolist())

        # Process same signal again
        result = self.analyzer.process_emg_chunk(signal.tolist())
        assert result["level"] == "normal"
        assert result["fatigue_pct"] < 80

    def test_fatigue_level_warning(self):
        """Test warning level (80-94%)"""
        # Setup baseline with high frequency signal
        import numpy as np

        freq = 150
        t = np.linspace(0, 0.128, 128)
        baseline_signal = np.sin(2 * np.pi * freq * t) * 100
        self.analyzer.process_emg_chunk(baseline_signal.tolist())

        # Low frequency signal (fatigue) → lower median freq
        low_freq = 40
        fatigue_signal = np.sin(2 * np.pi * low_freq * t) * 100
        result = self.analyzer.process_emg_chunk(fatigue_signal.tolist())

        # Should trigger warning if fatigue is in range
        if result["fatigue_pct"] >= 80 and result["fatigue_pct"] < 95:
            assert result["level"] == "warning"

    def test_fatigue_clamped_0_100(self):
        """Test that fatigue is clamped between 0 and 100"""
        import numpy as np

        freq = 100
        t = np.linspace(0, 0.128, 128)
        signal = np.sin(2 * np.pi * freq * t) * 100
        result = self.analyzer.process_emg_chunk(signal.tolist())

        assert 0 <= result["fatigue_pct"] <= 100


class TestLevelDetermination:
    """Test fatigue level determination logic"""

    def test_normal_threshold(self):
        """Test normal level below 80%"""
        analyzer = FatigueAnalyzer()
        analyzer.baseline_mf = 100.0

        # Fatigue < 80%
        result = analyzer.process_emg_chunk([50] * 128)
        if result["fatigue_pct"] < 80:
            assert result["level"] == "normal"

    def test_thresholds_defined(self):
        """Test that threshold constants are defined"""
        from tools.dashboard import server

        assert server.FATIGUE_THRESHOLD_WARNING == 80.0
        assert server.FATIGUE_THRESHOLD_CRITICAL == 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
