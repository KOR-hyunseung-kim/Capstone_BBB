"""
SSD1306 OLED Display Driver for BBB
Displays real-time EMG analysis results
"""

from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
import json


class OLEDDisplay:
    """
    SSD1306 OLED 128×64 display controller
    Shows fatigue percentage, Median Frequency, and status
    """

    def __init__(self, i2c: I2C, width: int = 128, height: int = 64, addr: int = 0x3C):
        """
        Initialize OLED display

        Args:
            i2c: Machine I2C object
            width: Display width (default 128)
            height: Display height (default 64)
            addr: I2C address (default 0x3C for SSD1306)
        """
        self.display = SSD1306_I2C(width, height, i2c, addr=addr)
        self.width = width
        self.height = height
        self.fatigue_pct = 0.0
        self.median_freq = 0.0
        self.level = "normal"
        self.mode = "Safety"
        self.blink_counter = 0

    def update(self, data: dict) -> None:
        """
        Update display with analysis results

        Args:
            data: {
                "fatigue_pct": float,
                "mf": float,
                "level": str,  # "normal" | "warning" | "critical"
            }
        """
        try:
            self.fatigue_pct = data.get("fatigue_pct", 0.0)
            self.median_freq = data.get("mf", 0.0)
            self.level = data.get("level", "normal")
            self.draw()
        except Exception as e:
            print(f"OLED update error: {e}")

    def draw(self) -> None:
        """Render display content"""
        self.display.fill(0)

        # Line 1: Mode indicator
        mode_text = "BBB  Safety Mode"
        self.display.text(mode_text, 0, 0, 1)

        # Line 2: Fatigue percentage + bar graph
        bar_width = self._fatigue_to_bar_width()
        fatigue_str = f"Fatigue: {self.fatigue_pct:5.1f}%"
        self.display.text(fatigue_str, 0, 16, 1)

        # Draw bar graph (horizontal, below fatigue text)
        bar_x, bar_y = 0, 26
        bar_height = 6
        bar_max_width = 128

        # Draw border
        self.display.rect(bar_x, bar_y, bar_max_width, bar_height, 1)

        # Draw filled portion
        if bar_width > 0:
            self.display.fill_rect(bar_x + 1, bar_y + 1, bar_width - 2, bar_height - 2, 1)

        # Line 3: Median Frequency
        mf_str = f"MF: {self.median_freq:6.2f} Hz"
        self.display.text(mf_str, 0, 38, 1)

        # Line 4: Status (with blink animation for CRITICAL)
        self.blink_counter += 1
        if self.level == "critical" and (self.blink_counter // 5) % 2 == 0:
            # Blink effect: hide text every other 5 frames (~250ms at 10fps)
            status_str = "              "
        else:
            status_map = {
                "normal": "OK",
                "warning": "WARNING",
                "critical": "CRITICAL!",
            }
            status_str = status_map.get(self.level, "?")

        self.display.text(status_str, 0, 54, 1)

        self.display.show()

    def _fatigue_to_bar_width(self) -> int:
        """Convert fatigue percentage (0~100) to bar width (0~128)"""
        return int((self.fatigue_pct / 100.0) * 128)

    def clear(self) -> None:
        """Clear display"""
        self.display.fill(0)
        self.display.show()

    def test_display(self) -> None:
        """Display test pattern for verification"""
        self.display.fill(0)

        # Test: all text sizes
        self.display.text("BBB OLED Test", 0, 0, 1)
        self.display.text("128x64", 0, 16, 1)
        self.display.text("SSD1306 Driver", 0, 32, 1)
        self.display.text("OK", 0, 54, 1)

        # Test bar
        self.display.rect(0, 48, 128, 6, 1)
        self.display.fill_rect(1, 49, 64, 4, 1)

        self.display.show()
