"""
MyoWare 2.0 EMG Sensor Driver for BBB
Analog EMG signal acquisition via ADC
"""

from machine import ADC, Pin
import time


class EMGSensor:
    """
    MyoWare 2.0 EMG sensor driver (analog output → ADC)
    Sampling rate: 1kHz, 12-bit ADC (0~4095)
    """

    def __init__(self, adc_pin: int, sample_rate: int = 1000):
        """
        Initialize EMG sensor

        Args:
            adc_pin: GPIO pin connected to MyoWare SIG output
            sample_rate: Sampling frequency in Hz (default 1000)
        """
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)  # 0~3.3V range
        self.adc.width(ADC.WIDTH_12BIT)  # 12-bit = 0~4095
        self.sample_rate = sample_rate
        self._interval_us = 1_000_000 // sample_rate

    def read_raw(self) -> int:
        """
        Read single ADC sample

        Returns:
            Raw ADC value (0~4095)
        """
        return self.adc.read()

    def read_mv(self) -> float:
        """
        Read EMG signal as voltage

        Returns:
            Signal voltage in millivolts
        """
        return self.adc.read() * 3300.0 / 4095.0

    def sample_chunk(self, n_samples: int = 100) -> list:
        """
        Acquire n_samples at 1kHz sampling rate

        Args:
            n_samples: Number of samples to collect

        Returns:
            List of raw ADC values
        """
        buf = []
        for _ in range(n_samples):
            buf.append(self.adc.read())
            time.sleep_us(self._interval_us)
        return buf

    def is_spike(self, threshold: int = 3500) -> bool:
        """
        Detect EMG spike (muscle contraction)

        Args:
            threshold: ADC value threshold for spike detection (default 3500)

        Returns:
            True if current sample exceeds threshold
        """
        return self.read_raw() > threshold

    def test_sensor(self) -> None:
        """Test sensor connectivity and output range"""
        samples = self.sample_chunk(10)
        avg = sum(samples) / len(samples)
        avg_mv = avg * 3300.0 / 4095.0
        print(
            f"EMG test: avg={avg:.0f} ({avg_mv:.0f}mV), range={min(samples)}-{max(samples)}"
        )
