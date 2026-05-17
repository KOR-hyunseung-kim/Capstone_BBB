"""
RGB LED Controller for BBB
Controls color-coded status indication
"""

from machine import Pin, PWM


class RGBLEDController:
    """
    RGB LED controller with PWM support
    Colors: Green (normal), Yellow (warning), Red (critical)
    """

    def __init__(
        self,
        red_pin,
        green_pin,
        blue_pin,
        frequency = 1000,
        inverted: bool = False,
    ):
        """
        Initialize RGB LED controller

        Args:
            red_pin: GPIO pin for red LED (PWM capable)
            green_pin: GPIO pin for green LED (PWM capable)
            blue_pin: GPIO pin for blue LED (PWM capable)
            frequency: PWM frequency (default 1000 Hz)
            inverted: True if using common-anode LED (rare), False for common-cathode
        """
        self.red_pwm = PWM(Pin(red_pin, Pin.OUT))
        self.green_pwm = PWM(Pin(green_pin, Pin.OUT))
        self.blue_pwm = PWM(Pin(blue_pin, Pin.OUT))

        self.red_pwm.freq(frequency)
        self.green_pwm.freq(frequency)
        self.blue_pwm.freq(frequency)

        self.inverted = inverted
        self._set_duty(0, 0, 0)

    def _set_duty(self, r, g, b):
        """Set PWM duty cycles (0~1023)"""
        if self.inverted:
            r, g, b = 1023 - r, 1023 - g, 1023 - b

        self.red_pwm.duty(r)
        self.green_pwm.duty(g)
        self.blue_pwm.duty(b)

    def set_color(self, level):
        """
        Set LED color based on fatigue level

        Args:
            level: "normal" (green), "warning" (yellow), "critical" (red)
        """
        colors = {
            "normal": (0, 1023, 0),  # Green
            "warning": (1023, 512, 0),  # Yellow (orange)
            "critical": (1023, 0, 0),  # Red
        }
        r, g, b = colors.get(level, (0, 0, 0))
        self._set_duty(r, g, b)

    def off(self):
        """Turn off LED"""
        self._set_duty(0, 0, 0)

    def set_rgb(self, r, g, b):
        """
        Directly set RGB values (0~1023)

        Args:
            r: Red intensity
            g: Green intensity
            b: Blue intensity
        """
        self._set_duty(r, g, b)

    def pulse(self, level, duration_ms = 500):
        """
        Pulse LED effect (for alert indication)

        Args:
            level: Fatigue level
            duration_ms: Pulse duration in milliseconds
        """
        import time

        colors = {
            "warning": (1023, 512, 0),
            "critical": (1023, 0, 0),
        }

        if level not in colors:
            return

        r, g, b = colors[level]
        steps = 10
        delay = duration_ms // (steps * 2)  # Pulse: up and down

        # Fade in
        for i in range(steps):
            intensity = int((r * i / steps, g * i / steps, b * i / steps))
            self._set_duty(int(r * i / steps), int(g * i / steps), int(b * i / steps))
            time.sleep_ms(delay)

        # Fade out
        for i in range(steps, 0, -1):
            self._set_duty(int(r * i / steps), int(g * i / steps), int(b * i / steps))
            time.sleep_ms(delay)

        self.off()
