"""
Vibration Motor Controller for BBB
Provides haptic feedback for fatigue alerts
"""

from machine import Pin, PWM
import time


class VibratorMotor:
    """
    Coin vibration motor (3V DC) controller via MOSFET PWM
    Patterns: single pulse, continuous vibration
    """

    def __init__(self, gpio_pin: int, frequency: int = 100):
        """
        Initialize vibration motor

        Args:
            gpio_pin: GPIO pin connected to MOSFET gate
            frequency: PWM frequency (default 100 Hz for motor)
        """
        self.pwm = PWM(Pin(gpio_pin, Pin.OUT))
        self.pwm.freq(frequency)
        self.pwm.duty(0)

    def single_pulse(self, duration_ms: int = 100, intensity: int = 800) -> None:
        """
        Single vibration pulse (1st alert)

        Args:
            duration_ms: Pulse duration in milliseconds
            intensity: PWM duty (0~1023), default 800 (weak)
        """
        self.pwm.duty(intensity)
        time.sleep_ms(duration_ms)
        self.pwm.duty(0)

    def double_pulse(self, interval_ms: int = 150, intensity: int = 900) -> None:
        """
        Double vibration pulse (stronger alert)

        Args:
            interval_ms: Time between pulses in milliseconds
            intensity: PWM duty (0~1023), default 900 (medium)
        """
        for _ in range(2):
            self.pwm.duty(intensity)
            time.sleep_ms(100)
            self.pwm.duty(0)
            time.sleep_ms(interval_ms)

    def continuous(self, duration_ms: int = 500, intensity: int = 1000) -> None:
        """
        Continuous vibration (urgent alert)

        Args:
            duration_ms: Vibration duration in milliseconds
            intensity: PWM duty (0~1023), default 1000 (max)
        """
        self.pwm.duty(intensity)
        time.sleep_ms(duration_ms)
        self.pwm.duty(0)

    def stop(self) -> None:
        """Stop vibration immediately"""
        self.pwm.duty(0)

    def alert_pattern(self, level: str) -> None:
        """
        Execute alert vibration based on fatigue level

        Args:
            level: "warning" or "critical"
        """
        if level == "warning":
            self.single_pulse(duration_ms=100, intensity=800)
        elif level == "critical":
            self.continuous(duration_ms=300, intensity=1000)

    def test_vibration(self) -> None:
        """Test vibration with increasing intensity"""
        intensities = [400, 600, 800, 1000]
        for intensity in intensities:
            self.pwm.duty(intensity)
            time.sleep_ms(200)
            self.pwm.duty(0)
            time.sleep_ms(100)
