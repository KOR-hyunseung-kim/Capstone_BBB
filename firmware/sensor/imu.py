"""
MPU6050 IMU Sensor Driver for MicroPython (ESP32-S3)
Reads 6-axis accelerometer and gyroscope data via I2C
"""

import math
from machine import I2C, Pin


class MPU6050:
    """MPU6050 6-axis IMU sensor driver."""

    # I2C slave address
    I2C_ADDR = 0x68

    # Register addresses
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43
    TEMP_OUT_H = 0x41

    def __init__(self, i2c_bus=None, sda_pin=21, scl_pin=22):
        """
        Initialize MPU6050 sensor.

        Args:
            i2c_bus: I2C instance (uses default pins if None)
            sda_pin: SDA pin number (default 21 for ESP32-S3)
            scl_pin: SCL pin number (default 22 for ESP32-S3)
        """
        if i2c_bus is None:
            try:
                # ESP32-S3 standard pins (21=SDA, 22=SCL)
                self.i2c = I2C(
                    0,
                    scl=Pin(scl_pin),
                    sda=Pin(sda_pin),
                    freq=400000,
                )
            except ValueError:
                # Fallback for different board configurations
                # Try alternative pins or slower frequency
                print(f"[WARN] Pins {sda_pin}/{scl_pin} not available, retrying...")
                try:
                    self.i2c = I2C(
                        0,
                        scl=Pin(scl_pin),
                        sda=Pin(sda_pin),
                        freq=100000,
                    )
                except Exception as e:
                    raise ValueError(
                        f"I2C initialization failed. "
                        f"Check pins: SDA={sda_pin}, SCL={scl_pin}. "
                        f"Error: {e}"
                    )
        else:
            self.i2c = i2c_bus

        self.addr = self.I2C_ADDR

        # Wake up MPU6050 (clear sleep bit)
        self.i2c.writeto(self.addr, bytes([self.PWR_MGMT_1, 0x00]))

        # Accelerometer scale: ±2g (sensitivity: 16384 LSB/g)
        self.accel_scale = 16384.0
        # Gyroscope scale: ±250 deg/s (sensitivity: 131 LSB/(deg/s))
        self.gyro_scale = 131.0

        # Calibration offsets
        self.accel_offset = [0.0, 0.0, 0.0]
        self.gyro_offset = [0.0, 0.0, 0.0]

    def _read_accel_gyro_temp(self):
        """
        Read raw accelerometer, gyroscope, and temperature data.

        Returns:
            (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, temp_c)
        """
        # Read 14 bytes from ACCEL_XOUT_H (0x3B to 0x48)
        data = self.i2c.readfrom_mem(self.addr, self.ACCEL_XOUT_H, 14)

        # Accelerometer (6 bytes: 0-5)
        ax = self._bytes_to_int16(data[0], data[1])
        ay = self._bytes_to_int16(data[2], data[3])
        az = self._bytes_to_int16(data[4], data[5])

        # Temperature (2 bytes: 6-7)
        temp_raw = self._bytes_to_int16(data[6], data[7])

        # Gyroscope (6 bytes: 8-13)
        gx = self._bytes_to_int16(data[8], data[9])
        gy = self._bytes_to_int16(data[10], data[11])
        gz = self._bytes_to_int16(data[12], data[13])

        # Convert temperature: (raw/340) + 36.53
        temp_c = (temp_raw / 340.0) + 36.53

        return ax, ay, az, gx, gy, gz, temp_c

    @staticmethod
    def _bytes_to_int16(high, low):
        """Convert two bytes to signed 16-bit integer."""
        value = (high << 8) | low
        if value > 32767:
            value = value - 65536
        return value

    def get_accel(self):
        """
        Get accelerometer data (m/s²).

        Returns:
            (ax, ay, az) in m/s²
        """
        ax, ay, az, _, _, _, _ = self._read_accel_gyro_temp()

        # Convert to m/s² (gravity ~9.81 m/s²)
        ax_mps2 = (ax / self.accel_scale) * 9.81 - self.accel_offset[0]
        ay_mps2 = (ay / self.accel_scale) * 9.81 - self.accel_offset[1]
        az_mps2 = (az / self.accel_scale) * 9.81 - self.accel_offset[2]

        return ax_mps2, ay_mps2, az_mps2

    def get_gyro(self):
        """
        Get gyroscope data (deg/s).

        Returns:
            (gx, gy, gz) in degrees per second
        """
        _, _, _, gx, gy, gz, _ = self._read_accel_gyro_temp()

        # Convert to deg/s
        gx_dps = (gx / self.gyro_scale) - self.gyro_offset[0]
        gy_dps = (gy / self.gyro_scale) - self.gyro_offset[1]
        gz_dps = (gz / self.gyro_scale) - self.gyro_offset[2]

        return gx_dps, gy_dps, gz_dps

    def get_temperature(self):
        """
        Get temperature reading (°C).

        Returns:
            Temperature in Celsius
        """
        _, _, _, _, _, _, temp_c = self._read_accel_gyro_temp()
        return temp_c

    def get_all(self):
        """
        Get all sensor data at once.

        Returns:
            (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, temp_c)
        """
        ax, ay, az, gx, gy, gz, temp = self._read_accel_gyro_temp()

        ax_mps2 = (ax / self.accel_scale) * 9.81 - self.accel_offset[0]
        ay_mps2 = (ay / self.accel_scale) * 9.81 - self.accel_offset[1]
        az_mps2 = (az / self.accel_scale) * 9.81 - self.accel_offset[2]

        gx_dps = (gx / self.gyro_scale) - self.gyro_offset[0]
        gy_dps = (gy / self.gyro_scale) - self.gyro_offset[1]
        gz_dps = (gz / self.gyro_scale) - self.gyro_offset[2]

        return ax_mps2, ay_mps2, az_mps2, gx_dps, gy_dps, gz_dps, temp

    def calibrate_accel(self, samples=100):
        """
        Calibrate accelerometer (device should be stationary).

        Args:
            samples: Number of samples to average
        """
        print("Calibrating accelerometer (keep device stationary)...")
        sum_x, sum_y, sum_z = 0.0, 0.0, 0.0

        for _ in range(samples):
            ax, ay, az = self.get_accel()
            sum_x += ax
            sum_y += ay
            sum_z += az

        avg_x = sum_x / samples
        avg_y = sum_y / samples
        avg_z = sum_z / samples

        # Z-axis should be ~9.81 m/s² when stationary
        self.accel_offset[0] = avg_x
        self.accel_offset[1] = avg_y
        self.accel_offset[2] = avg_z - 9.81

        print(
            f"Calibration complete: offsets = "
            f"({self.accel_offset[0]:.3f}, "
            f"{self.accel_offset[1]:.3f}, "
            f"{self.accel_offset[2]:.3f})"
        )

    def calibrate_gyro(self, samples=100):
        """
        Calibrate gyroscope (device should be stationary).

        Args:
            samples: Number of samples to average
        """
        print("Calibrating gyroscope (keep device stationary)...")
        sum_x, sum_y, sum_z = 0.0, 0.0, 0.0

        for _ in range(samples):
            gx, gy, gz = self.get_gyro()
            sum_x += gx
            sum_y += gy
            sum_z += gz

        self.gyro_offset[0] = sum_x / samples
        self.gyro_offset[1] = sum_y / samples
        self.gyro_offset[2] = sum_z / samples

        print(
            f"Calibration complete: offsets = "
            f"({self.gyro_offset[0]:.3f}, "
            f"{self.gyro_offset[1]:.3f}, "
            f"{self.gyro_offset[2]:.3f})"
        )
