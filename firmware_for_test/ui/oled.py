"""
SSD1306 OLED Display Driver for BBB
Displays real-time EMG analysis results

MicroPython compatible - ssd1306 driver embedded
"""

from machine import I2C, Pin
import json
from micropython import const
import framebuf

# SSD1306 Control Codes
SET_CONTRAST = const(0x81)
SET_NORMAL_DISPLAY = const(0xA6)
SET_INVERT_DISPLAY = const(0xA7)
SET_DISPLAY_OFF = const(0xAE)
SET_DISPLAY_ON = const(0xAF)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA1)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC8)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)
SET_MEMORY_ADDR_MODE = const(0x20)
SET_COLUMN_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)


class SSD1306:
    """Embedded SSD1306 OLED driver"""
    def __init__(self, width, height, i2c, addr=0x3c):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(width * self.pages)
        self.framebuf = framebuf.FrameBuffer(self.buffer, width, height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        import time

        # 공식 SSD1306 초기화 시퀀스 (안정적)
        init_sequence = [
            0xAE,           # 0: Set display OFF
            0xD5, 0x80,     # 1-2: Set clock divide ratio
            0xA8, 0x3F,     # 3-4: Set multiplex ratio (1/64)
            0xD3, 0x00,     # 5-6: Set display offset
            0x40,           # 7: Set start line address
            0x8D, 0x14,     # 8-9: Set charge pump enable
            0x20, 0x00,     # 10-11: Memory addressing mode (horizontal)
            0xA1,           # 12: Set segment remap
            0xC8,           # 13: Set COM output direction
            0xDA, 0x12,     # 14-15: Set COM pins
            0x81, 0x7F,     # 16-17: Set contrast (brightness)
            0xD9, 0xF1,     # 18-19: Set precharge period
            0xDB, 0x40,     # 20-21: Set VCOM deselect
            0xA4,           # 22: Resume to RAM content display
            0xA6,           # 23: Normal display (not inverted)
            0xAF,           # 24: Turn ON display
        ]

        for byte in init_sequence:
            self.write_cmd(byte)
            time.sleep(0.001)  # 각 명령어 사이 1ms 대기

        time.sleep(0.1)  # 초기화 완료 대기

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def write_data(self, buf):
        # I2C 데이터 전송 (청크 단위로 나눠서 전송 - 안정성 증가)
        import time
        chunk_size = 16  # 한 번에 16바이트씩 전송
        header = bytes([0x40])

        for i in range(0, len(buf), chunk_size):
            chunk = buf[i:i + chunk_size]
            try:
                self.i2c.writeto(self.addr, header + chunk)
                time.sleep(0.001)  # 청크 사이 1ms 대기
            except Exception as e:
                # 전송 실패해도 계속 진행
                pass

    def show(self):
        self.write_cmd(SET_COLUMN_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.width - 1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

    def fill(self, col):
        self.framebuf.fill(col)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def rect(self, x, y, w, h, col):
        self.framebuf.rect(x, y, w, h, col)

    def fill_rect(self, x, y, w, h, col):
        self.framebuf.fill_rect(x, y, w, h, col)


class SSD1306_I2C(SSD1306):
    """I2C variant of SSD1306"""
    pass


# Try to initialize real display
HAS_SSD1306 = True
try:
    # Just verify the driver is available
    _ = SSD1306_I2C
except Exception:
    print("[Warning] SSD1306 initialization failed - using mock display")
    HAS_SSD1306 = False

    # Fallback: Mock SSD1306 for testing without hardware
    class SSD1306_I2C:
        def __init__(self, width, height, i2c, addr=0x3C):
            self.width = width
            self.height = height
            self.addr = addr

        def fill(self, color):
            pass

        def text(self, text, x, y, color):
            pass

        def rect(self, x, y, w, h, color):
            pass

        def fill_rect(self, x, y, w, h, color):
            pass

        def show(self):
            pass


class OLEDDisplay:
    """
    SSD1306 OLED 128x64 display controller
    Shows fatigue percentage, Median Frequency, and status
    Falls back to mock display if ssd1306 library unavailable
    """

    def __init__(self, i2c, width=128, height=64, addr=0x3C):
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
        self.is_mock = not HAS_SSD1306

        if self.is_mock:
            print("[OLED] Using mock display (no ssd1306 library)")

    def update(self, data):
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

    def draw(self):
        """Render display content - Clean centered layout (monochrome)"""
        if self.is_mock:
            return

        self.display.fill(0)

        # 상단: 모드 표시
        self.display.text("BBB Safety Mode", 8, 2, 1)

        # 중단: 큰 % 값 (센터)
        fatigue_str = f"{self.fatigue_pct:.1f}%"
        text_width = len(fatigue_str) * 6
        x_pos = (128 - text_width) // 2
        self.display.text(fatigue_str, x_pos, 16, 1)

        # 프로그레스 바
        bar_x, bar_y = 8, 30
        bar_max_width = 112
        bar_height = 6

        self.display.rect(bar_x, bar_y, bar_max_width, bar_height, 1)
        if self.fatigue_pct > 0:
            fill_width = int((self.fatigue_pct / 100.0) * (bar_max_width - 2))
            if fill_width > 0:
                self.display.fill_rect(bar_x + 1, bar_y + 1, fill_width, bar_height - 2, 1)

        # 상태 텍스트 (센터)
        self.blink_counter += 1
        if self.level == "critical" and (self.blink_counter // 4) % 2 == 0:
            status_str = ""
        else:
            status_map = {
                "normal": "OK",
                "warning": "WARNING",
                "critical": "CRITICAL!",
            }
            status_str = status_map.get(self.level, "?")

        if status_str:
            status_width = len(status_str) * 6
            status_x = (128 - status_width) // 2
            self.display.text(status_str, status_x, 44, 1)

        # 하단 정보
        self.display.text(f"MF:{self.median_freq:5.0f}Hz", 2, 56, 1)

        self.display.show()

    def show_message(self, text1, text2="", text3=""):
        """Display custom message on OLED (for setup, calibration, etc)"""
        if self.is_mock:
            return

        self.display.fill(0)

        if text1:
            self.display.text(text1, 8, 16, 1)
        if text2:
            self.display.text(text2, 8, 32, 1)
        if text3:
            self.display.text(text3, 8, 48, 1)

        self.display.show()

    def show_progress(self, title, percent):
        """Display progress bar with title"""
        if self.is_mock:
            return

        self.display.fill(0)

        # 제목
        self.display.text(title, 8, 8, 1)

        # 진행률 (%)
        progress_str = f"{percent:.0f}%"
        progress_x = (128 - len(progress_str) * 6) // 2
        self.display.text(progress_str, progress_x, 24, 1)

        # 프로그레스 바
        bar_x, bar_y = 8, 40
        bar_max_width = 112
        bar_height = 8

        self.display.rect(bar_x, bar_y, bar_max_width, bar_height, 1)
        if percent > 0:
            fill_width = int((percent / 100.0) * (bar_max_width - 2))
            if fill_width > 0:
                self.display.fill_rect(bar_x + 1, bar_y + 1, fill_width, bar_height - 2, 1)

        self.display.show()

    def _fatigue_to_bar_width(self):
        """Convert fatigue percentage (0~100) to bar width (0~128)"""
        return int((self.fatigue_pct / 100.0) * 128)

    def clear(self):
        """Clear display"""
        if not self.is_mock:
            self.display.fill(0)
            self.display.show()

    def test_display(self):
        """Display test pattern for verification"""
        if self.is_mock:
            print("[OLED] Test display (mock mode)")
            return

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
