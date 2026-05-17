"""
ICM-20602 6-axis IMU Sensor Driver for MicroPython (ESP32-S3)
Higher performance than MPU6050 (lower noise, better accuracy)
I2C Interface (SPI not implemented)

Pin Configuration (I2C mode):
  VCC   → 3.3V
  GND   → GND
  SDA   → GPIO 8
  SCL   → GPIO 9
  SAO   → GND (for I2C addr 0x68) or VCC (for 0x69)
  INT   → (optional, not used)
  CS    → (pull HIGH for I2C mode)
  FSY   → (optional, not used)
"""

from machine import I2C, Pin
import math


class ICM20602:
    """ICM-20602 6-axis IMU sensor driver (I2C mode)."""

    # I2C Address
    I2C_ADDR_AD0_LOW = 0x68  # SAO connected to GND
    I2C_ADDR_AD0_HIGH = 0x69  # SAO connected to VCC

    # Register Addresses
    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C
    ACCEL_XOUT_H = 0x3B
    TEMP_OUT_H = 0x41
    GYRO_XOUT_H = 0x43
    WHO_AM_I = 0x75

    # Expected WHO_AM_I value
    WHOAMI_VALUE = 0x12  # ICM-20602

    def __init__(self, i2c_bus=None, sda_pin=8, scl_pin=9, addr=None):
        """
        Initialize ICM-20602 sensor.

        Args:
            i2c_bus: I2C instance (creates new if None)
            sda_pin: SDA pin (default 8 for ESP32-S3)
            scl_pin: SCL pin (default 9 for ESP32-S3)
            addr: I2C address (0x68 or 0x69, auto-detect if None)
        """
        if i2c_bus is None:
            try:
                self.i2c = I2C(
                    0,
                    scl=Pin(scl_pin),
                    sda=Pin(sda_pin),
                    freq=400000,
                )
            except ValueError:
                # Retry with slower frequency
                self.i2c = I2C(
                    0,
                    scl=Pin(scl_pin),
                    sda=Pin(sda_pin),
                    freq=100000,
                )
        else:
            self.i2c = i2c_bus

        # Auto-detect address if not provided
        if addr is None:
            self.addr = self._detect_address()
        else:
            self.addr = addr

        # Verify sensor
        self._verify_sensor()

        # Sensor scales
        # Accelerometer: ±2g, 16384 LSB/g
        self.accel_scale = 16384.0
        # Gyroscope: ±250 deg/s, 131 LSB/(deg/s)
        self.gyro_scale = 131.0

        # Calibration offsets
        self.accel_offset = [0.0, 0.0, 0.0]
        self.gyro_offset = [0.0, 0.0, 0.0]

        # Initialize sensor
        self._init_sensor()

    def _detect_address(self):
        """Auto-detect sensor address (0x68 or 0x69)."""
        addresses = [self.I2C_ADDR_AD0_LOW, self.I2C_ADDR_AD0_HIGH]

        for addr in addresses:
            try:
                whoami = self.i2c.readfrom_mem(addr, self.WHO_AM_I, 1)[0]
                if whoami == self.WHOAMI_VALUE:
                    print(f"[OK] ICM-20602 found at 0x{addr:02x}")
                    return addr
            except Exception:
                continue

        raise RuntimeError(
            "ICM-20602 not found at 0x68 or 0x69. "
            "Check I2C connection and SAO pin."
        )

    def _verify_sensor(self):
        """Verify sensor is ICM-20602."""
        try:
            whoami = self.i2c.readfrom_mem(self.addr, self.WHO_AM_I, 1)[0]
            if whoami != self.WHOAMI_VALUE:
                raise RuntimeError(
                    f"Invalid sensor. WHO_AM_I = 0x{whoami:02x}, "
                    f"expected 0x{self.WHOAMI_VALUE:02x}. "
                    f"This may be MPU6050 (0x71) instead."
                )
        except Exception as e:
            raise RuntimeError(f"Cannot read WHO_AM_I: {e}")

    def _init_sensor(self):
        """Initialize sensor (wake up, configure)."""
        # Wake up (clear SLEEP bit)
        self.i2c.writeto_mem(self.addr, self.PWR_MGMT_1, bytes([0x00]))

        # Enable all sensors (disable standby)
        self.i2c.writeto_mem(self.addr, self.PWR_MGMT_2, bytes([0x00]))

        print("[OK] ICM-20602 initialized and ready")

    def _read_accel_gyro_temp(self):
        """
        Read raw accelerometer, gyroscope, and temperature.

        Returns:
            (ax, ay, az, gx, gy, gz, temp_c)
        """
        # Read 14 bytes from ACCEL_XOUT_H (0x3B to 0x48)
        data = self.i2c.readfrom_mem(self.addr, self.ACCEL_XOUT_H, 14)

        # Accelerometer (bytes 0-5)
        ax = self._bytes_to_int16(data[0], data[1])
        ay = self._bytes_to_int16(data[2], data[3])
        az = self._bytes_to_int16(data[4], data[5])

        # Temperature (bytes 6-7)
        temp_raw = self._bytes_to_int16(data[6], data[7])

        # Gyroscope (bytes 8-13)
        gx = self._bytes_to_int16(data[8], data[9])
        gy = self._bytes_to_int16(data[10], data[11])
        gz = self._bytes_to_int16(data[12], data[13])

        # Temperature formula: (raw - 0) / 326.8 + 25
        temp_c = temp_raw / 326.8 + 25.0

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
        Calibrate accelerometer (keep device stationary).

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
            f"[OK] Calibration complete: offsets = "
            f"({self.accel_offset[0]:.3f}, "
            f"{self.accel_offset[1]:.3f}, "
            f"{self.accel_offset[2]:.3f})"
        )

    def calibrate_gyro(self, samples=100):
        """
        Calibrate gyroscope (keep device stationary).

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
            f"[OK] Gyro calibration complete: offsets = "
            f"({self.gyro_offset[0]:.3f}, "
            f"{self.gyro_offset[1]:.3f}, "
            f"{self.gyro_offset[2]:.3f})"
        )


# Compatibility: if someone imports as MPU6050, use ICM20602
MPU6050 = ICM20602
