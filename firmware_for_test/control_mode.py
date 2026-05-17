"""
Control Mode - IMU-based Cursor Control with EMG Click Detection
Arm tilt (IMU) → cursor movement, Muscle contraction (EMG spike) → click
"""

import time
import math
from sensor.emg import EMGSensor
from ui.led import RGBLEDController
from ui.motor import VibratorMotor
from machine import Pin
import config

# Import appropriate IMU driver based on config
if config.IMU_TYPE == "ICM20602":
    try:
        from sensor.icm20602 import ICM20602 as IMUSensor
    except ImportError:
        print("[Warning] ICM20602 not found, falling back to MPU6050")
        from sensor.imu import MPU6050 as IMUSensor
else:
    from sensor.imu import MPU6050 as IMUSensor


class ComplementaryFilter:
    """Complementary filter for angle fusion (accelerometer + gyroscope)"""

    def __init__(self, alpha=0.98, dt=0.01):
        """
        Initialize complementary filter

        Args:
            alpha: Weight for gyroscope integration (0~1, typically 0.95~0.99)
            dt: Time delta for integration (seconds)
        """
        self.alpha = alpha
        self.dt = dt
        self.pitch = 0.0
        self.roll = 0.0

    def update(self, ax, ay, az, gx, gy, gz):
        """
        Update angles using complementary filter

        Args:
            ax, ay, az: Accelerometer data (m/s²)
            gx, gy, gz: Gyroscope data (deg/s)

        Returns:
            (pitch, roll) in degrees
        """
        # Calculate angles from accelerometer (static reference)
        # Pitch: forward/backward tilt
        ax_pitch = math.atan2(ay, math.sqrt(ax**2 + az**2)) * 180 / math.pi
        # Roll: left/right tilt
        ay_roll = math.atan2(ax, math.sqrt(ay**2 + az**2)) * 180 / math.pi

        # Complementary filter: fuse accel (long-term) + gyro (short-term)
        # Pitch = alpha * (prev_pitch + gyro_gy * dt) + (1-alpha) * accel_pitch
        self.pitch = (
            self.alpha * (self.pitch + gy * self.dt)
            + (1 - self.alpha) * ax_pitch
        )
        # Roll = alpha * (prev_roll + gyro_gx * dt) + (1-alpha) * accel_roll
        self.roll = (
            self.alpha * (self.roll + gx * self.dt) + (1 - self.alpha) * ay_roll
        )

        return self.pitch, self.roll


class ControlMode:
    """
    Control Mode: IMU-based arm tilt control + EMG spike click detection
    - Pitch (forward/backward): Cursor Y movement
    - Roll (left/right): Cursor X movement
    - EMG spike: Mouse click
    """

    def __init__(self):
        """Initialize sensors and controllers"""
        # EMG Sensor
        self.emg = None
        if config.ENABLE_EMG_SENSOR:
            try:
                self.emg = EMGSensor(config.EMG_ADC_PIN, sample_rate=config.EMG_SAMPLE_RATE)
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[ControlMode] EMG sensor initialized")
            except Exception as e:
                print(f"[ControlMode] EMG sensor failed: {e}")

        # IMU Sensor (MPU6050 or ICM20602)
        self.imu = None
        if config.ENABLE_IMU_SENSOR:
            try:
                self.imu = IMUSensor(
                    sda_pin=config.I2C_SDA_PIN, scl_pin=config.I2C_SCL_PIN
                )
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[ControlMode] IMU sensor (%s) initialized" % config.IMU_TYPE)
            except Exception as e:
                print(f"[ControlMode] IMU sensor failed: {e}")
                self.imu = None

        # RGB LED
        self.led = None
        if config.ENABLE_LED:
            try:
                self.led = RGBLEDController(
                    config.LED_RED_PIN,
                    config.LED_GREEN_PIN,
                    config.LED_BLUE_PIN,
                    frequency=1000,
                    inverted=False,
                )
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[ControlMode] LED controller initialized")
            except Exception as e:
                print(f"[ControlMode] LED controller failed: {e}")
                self.led = None

        # Vibration Motor
        self.motor = None
        if config.ENABLE_MOTOR:
            try:
                self.motor = VibratorMotor(config.VIBRATOR_PIN, frequency=100)
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[ControlMode] Motor controller initialized")
            except Exception as e:
                print(f"[ControlMode] Motor controller failed: {e}")

        # Mode Switch
        try:
            self.mode_switch = Pin(config.MODE_SWITCH_PIN, Pin.IN, Pin.PULL_UP)
        except Exception as e:
            print(f"[ControlMode] Mode switch failed: {e}")
            self.mode_switch = None

        # IMU angle filter
        self.filter = ComplementaryFilter(
            alpha=config.COMPLEMENTARY_FILTER_ALPHA,
            dt=config.COMPLEMENTARY_FILTER_DT
        )

        # Control state
        self.pitch = 0.0
        self.roll = 0.0
        self.cursor_x = 512  # Center of 0~1024 range
        self.cursor_y = 512
        self.click_detected = False
        self.last_click_time = 0
        self.click_cooldown_ms = 200  # Prevent rapid-fire clicks

        # EMG spike threshold
        self.emg_spike_threshold = config.EMG_SPIKE_THRESHOLD

        # Cursor speed (pixels per degree)
        self.cursor_speed = config.CURSOR_SPEED_FACTOR

        # LED state
        self.led_state = "ready"  # "ready", "click", "error"

        print("[ControlMode] Initialized (IMU=%s, EMG=%s, LED=%s, Motor=%s)" %
              (config.ENABLE_IMU_SENSOR, config.ENABLE_EMG_SENSOR,
               config.ENABLE_LED, config.ENABLE_MOTOR))

    def calibrate(self, duration_sec=5):
        """
        IMU calibration: collect baseline data while arm is at rest

        Args:
            duration_sec: Calibration duration in seconds
        """
        if not config.ENABLE_IMU_SENSOR or not self.imu:
            print("[ControlMode] IMU disabled - skipping calibration")
            return

        if config.DEBUG and config.DEBUG_CALIBRATION:
            print(f"[ControlMode] IMU calibration starting ({duration_sec}s)...")
            print("[ControlMode] Keep arm relaxed and level")

        if self.led:
            self.led.set_color("normal")  # Green during calibration

        # Accelerometer calibration
        self.imu.calibrate_accel(samples=50)

        # Gyroscope calibration (optional, but recommended)
        self.imu.calibrate_gyro(samples=50)

        if config.DEBUG and config.DEBUG_CALIBRATION:
            print("[ControlMode] Calibration complete. Ready for cursor control.")

    def update(self):
        """
        Process one control cycle

        Returns:
            dict: Current status (pitch, roll, cursor_x, cursor_y, click)
        """
        # Read IMU
        if not config.ENABLE_IMU_SENSOR or not self.imu:
            if self.led:
                self.led.set_color("critical")
            return {
                "mode": "control",
                "error": True,
                "message": "IMU sensor disabled",
            }

        try:
            ax, ay, az, gx, gy, gz, temp = self.imu.get_all()
        except Exception as e:
            print(f"[ControlMode] IMU read error: {e}")
            if self.led:
                self.led.set_color("critical")
            return {
                "mode": "control",
                "error": True,
                "message": "IMU communication failed",
            }

        # Update angles using complementary filter
        self.pitch, self.roll = self.filter.update(ax, ay, az, gx, gy, gz)

        # Calculate cursor movement from angles
        # Pitch (forward/backward) → Y movement
        cursor_dy = int(self.pitch * self.cursor_speed)
        # Roll (left/right) → X movement
        cursor_dx = int(self.roll * self.cursor_speed)

        # Update cursor position (bounded to 0~1024)
        self.cursor_x = max(0, min(1024, 512 + cursor_dx))
        self.cursor_y = max(0, min(1024, 512 + cursor_dy))

        # Check for EMG spike (click trigger)
        emg_raw = 0
        if config.ENABLE_EMG_SENSOR and self.emg:
            emg_raw = self.emg.read_raw()
            self.click_detected = emg_raw > self.emg_spike_threshold

            current_time = time.ticks_ms()
            time_since_click = time.ticks_diff(current_time, self.last_click_time)

            if self.click_detected and time_since_click > self.click_cooldown_ms:
                # Click detected and cooldown elapsed
                self.last_click_time = current_time
                self._trigger_click()
        else:
            self.click_detected = False

        # Update LED state
        if config.ENABLE_LED and self.led:
            if self.click_detected:
                self.led.set_color("warning")  # Yellow during click
                self.led_state = "click"
            else:
                self.led.set_color("normal")  # Green while ready
                self.led_state = "ready"

        # Debug output
        if config.DEBUG and config.DEBUG_CONTROL_MODE:
            print(
                f"[ControlMode] Pitch: {self.pitch:6.1f}°, Roll: {self.roll:6.1f}°, "
                f"Cursor: ({self.cursor_x}, {self.cursor_y}), "
                f"EMG: {emg_raw:4d}, Click: {self.click_detected}"
            )

        return {
            "mode": "control",
            "pitch": self.pitch,
            "roll": self.roll,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "emg_raw": emg_raw,
            "click_detected": self.click_detected,
            "led_state": self.led_state,
        }

    def _trigger_click(self):
        """Execute click feedback (motor + LED pulse)"""
        if not config.ENABLE_MOTOR or not self.motor:
            return

        # Vibration feedback
        self.motor.single_pulse(
            duration_ms=100, intensity=config.MOTOR_WARNING_INTENSITY
        )

        if config.DEBUG and config.DEBUG_CONTROL_MODE and config.DEBUG_MOTOR_CONTROL:
            print("[ControlMode] Click! Motor pulse sent")

    def normalize_cursor(self, x, y):
        """
        Normalize cursor position to 0~1 range

        Args:
            x, y: Raw cursor position (0~1024)

        Returns:
            (x_norm, y_norm): Normalized 0~1 range
        """
        x_norm = x / 1024.0
        y_norm = y / 1024.0
        return x_norm, y_norm

    def check_mode_switch(self):
        """
        Check if mode switch was pressed

        Returns:
            True if switch pressed (transition to Safety Mode)
        """
        if not self.mode_switch:
            return False
        return self.mode_switch.value() == 0  # LOW when pressed

    def cleanup(self):
        """Stop all feedback and reset state"""
        if config.ENABLE_MOTOR and self.motor:
            self.motor.stop()
        if config.ENABLE_LED and self.led:
            self.led.off()
        print("[ControlMode] Cleanup complete")


def control_mode_loop(duration_sec=None):
    """
    Main Control Mode loop

    Args:
        duration_sec: Run for N seconds (None = infinite, until mode switch)
    """
    mode = ControlMode()

    # IMU calibration phase
    print("[ControlMode] Starting IMU calibration...")
    mode.calibrate(duration_sec=5)

    # Control phase
    print("[ControlMode] Entering cursor control phase...")
    print("[ControlMode] Tilt arm to move cursor, clench fist to click")
    start_time = time.time()

    try:
        while True:
            # Check mode switch
            if mode.check_mode_switch():
                print("[ControlMode] Mode switch detected - transitioning to Safety Mode")
                mode.cleanup()
                return "safety"

            # Update control state
            status = mode.update()

            # Check duration limit
            if duration_sec and (time.time() - start_time) > duration_sec:
                print("[ControlMode] Duration limit reached")
                mode.cleanup()
                return "stop"

            # Sleep briefly to prevent CPU saturation
            # IMU sampling at ~100 Hz = 10ms interval
            time.sleep_ms(10)

    except KeyboardInterrupt:
        print("[ControlMode] Interrupted by user")
        mode.cleanup()
        return "stop"
