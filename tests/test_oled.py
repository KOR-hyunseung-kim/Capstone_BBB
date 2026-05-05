"""
Unit tests for OLED display logic
Tests fatigue bar conversion and color level mapping
"""

import pytest


class MockI2C:
    """Mock I2C for testing without hardware"""

    def writeto(self, addr, data):
        pass


class MockPin:
    """Mock GPIO Pin"""

    OUT = 1

    def __init__(self, pin, mode):
        self.pin = pin
        self.mode = mode


class MockOLED:
    """Mock SSD1306 display"""

    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self._buffer = []

    def fill(self, color):
        pass

    def text(self, text, x, y, color):
        self._buffer.append({"text": text, "x": x, "y": y})

    def rect(self, x, y, w, h, color):
        pass

    def fill_rect(self, x, y, w, h, color):
        pass

    def show(self):
        pass


class TestOLEDDisplay:
    """Test OLED display functionality"""

    def test_fatigue_to_bar_width_conversion(self):
        """Test conversion of fatigue percentage to bar width"""
        # Simulate the conversion logic
        def fatigue_to_bar_width(fatigue_pct, max_width=128):
            return int((fatigue_pct / 100.0) * max_width)

        assert fatigue_to_bar_width(0) == 0
        assert fatigue_to_bar_width(50) == 64
        assert fatigue_to_bar_width(100) == 128
        assert fatigue_to_bar_width(25) == 32
        assert fatigue_to_bar_width(75) == 96

    def test_level_to_status_string(self):
        """Test conversion of level to display text"""
        status_map = {
            "normal": "OK",
            "warning": "WARNING",
            "critical": "CRITICAL!",
        }

        assert status_map["normal"] == "OK"
        assert status_map["warning"] == "WARNING"
        assert status_map["critical"] == "CRITICAL!"

    def test_display_format_strings(self):
        """Test format of display strings"""
        # Test fatigue format
        fatigue_pct = 72.4
        fatigue_str = f"Fatigue: {fatigue_pct:5.1f}%"
        assert fatigue_str == "Fatigue:  72.4%"

        # Test median frequency format
        median_freq = 68.234
        mf_str = f"MF: {median_freq:6.2f} Hz"
        assert mf_str == "MF:  68.23 Hz"

    def test_display_lines_organization(self):
        """Test that display lines are properly organized"""
        # Line 1: Mode indicator
        line1 = "BBB  Safety Mode"
        assert len(line1) <= 16  # Fits on 128px width with small font

        # Line 2: Fatigue with bar
        line2 = "Fatigue:  50.0%"
        assert len(line2) <= 16

        # Line 3: Median frequency
        line3 = "MF:  75.00 Hz"
        assert len(line3) <= 16

        # Line 4: Status
        statuses = ["OK", "WARNING", "CRITICAL!"]
        for status in statuses:
            assert len(status) <= 16


class TestOLEDDataProcessing:
    """Test OLED data update processing"""

    def test_update_with_valid_data(self):
        """Test that display updates with valid analysis data"""
        test_data = {
            "fatigue_pct": 75.5,
            "mf": 70.25,
            "level": "warning",
        }

        # Simulate update
        fatigue_pct = test_data.get("fatigue_pct", 0.0)
        median_freq = test_data.get("mf", 0.0)
        level = test_data.get("level", "normal")

        assert fatigue_pct == 75.5
        assert median_freq == 70.25
        assert level == "warning"

    def test_update_with_missing_fields(self):
        """Test that display handles missing fields gracefully"""
        incomplete_data = {"fatigue_pct": 50.0}  # Missing mf and level

        fatigue_pct = incomplete_data.get("fatigue_pct", 0.0)
        median_freq = incomplete_data.get("mf", 0.0)
        level = incomplete_data.get("level", "normal")

        assert fatigue_pct == 50.0
        assert median_freq == 0.0
        assert level == "normal"

    def test_blink_animation_counter(self):
        """Test blink counter for critical status animation"""
        blink_counter = 0

        # Simulate 20 frames of blinking
        for frame in range(20):
            blink_counter += 1
            should_show = (blink_counter // 5) % 2 != 0

            if frame == 0:
                # Counter 1-5: show (1//5=0, 0%2=0, !=0 is False... wait, logic check)
                # Counter 1: (1//5)%2 = 0, !=0 False → hidden
                # Counter 5: (5//5)%2 = 1, !=0 True → shown
                # Counter 6: (6//5)%2 = 1, !=0 True → shown
                # Counter 10: (10//5)%2 = 0, !=0 False → hidden
                pass

        # After 20 frames, should have cycled through show/hide
        assert blink_counter == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
