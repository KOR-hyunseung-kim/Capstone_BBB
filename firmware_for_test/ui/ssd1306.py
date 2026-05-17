# MicroPython SSD1306 OLED display driver
# Simplified version for ESP32

from micropython import const
import framebuf

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
        for byte in [
            SET_DISP_CLK_DIV, 0x80,
            SET_MUX_RATIO, self.height - 1,
            SET_DISP_OFFSET, 0x00,
            SET_DISP_START_LINE | 0x00,
            SET_CHARGE_PUMP, 0x14,
            SET_MEMORY_ADDR_MODE, 0x02,
            SET_SEG_REMAP | 0x01,
            SET_COM_OUT_DIR,
            SET_COM_PIN_CFG, 0x12 if self.height == 32 else 0x12,
            SET_CONTRAST, 0x7f,
            SET_PRECHARGE, 0xf1,
            SET_VCOM_DESEL, 0x20,
            SET_NORMAL_DISPLAY,
            SET_DISPLAY_ON,
        ]:
            self.write_cmd(byte)

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def write_data(self, buf):
        self.i2c.writeto(self.addr, bytes([0x40]) + buf)

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COLUMN_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def hline(self, x, y, w, col):
        self.framebuf.hline(x, y, w, col)

    def vline(self, x, y, h, col):
        self.framebuf.vline(x, y, h, col)

    def rect(self, x, y, w, h, col):
        self.framebuf.rect(x, y, w, h, col)

    def fill_rect(self, x, y, w, h, col):
        self.framebuf.fill_rect(x, y, w, h, col)

    def line(self, x1, y1, x2, y2, col):
        self.framebuf.line(x1, y1, x2, y2, col)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c):
        super().__init__(width, height, i2c, addr)
