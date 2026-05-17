"""
Safety Mode - EMG Fatigue Monitoring with LED & Motor Feedback
Continuous muscle fatigue detection with visual + haptic alerts
"""

import time
from sensor.emg import EMGSensor
from ui.led import RGBLEDController
from ui.motor import VibratorMotor
from machine import Pin
from comm.wifi import WiFiManager
import config


class SafetyMode:
    """
    Monitors EMG signal and provides fatigue-based feedback
    LED: Green (normal) → Yellow (warning) → Red (critical)
    Motor: Silent → Short pulses (long interval) → Short pulses (short interval)
    """

    def __init__(self):
        """Initialize sensors and controllers"""
        # EMG Sensor
        self.emg = None
        if config.ENABLE_EMG_SENSOR:
            try:
                self.emg = EMGSensor(config.EMG_ADC_PIN, sample_rate=config.EMG_SAMPLE_RATE)
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[SafetyMode] EMG sensor initialized")
            except Exception as e:
                print(f"[SafetyMode] EMG sensor failed: {e}")
                self.emg = None

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
                    print("[SafetyMode] LED controller initialized")
            except Exception as e:
                print(f"[SafetyMode] LED controller failed: {e}")
                self.led = None

        # Vibration Motor
        self.motor = None
        if config.ENABLE_MOTOR:
            try:
                self.motor = VibratorMotor(config.VIBRATOR_PIN, frequency=100)
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[SafetyMode] Motor controller initialized")
            except Exception as e:
                print(f"[SafetyMode] Motor controller failed: {e}")
                self.motor = None

        # Mode Switch
        try:
            self.mode_switch = Pin(config.MODE_SWITCH_PIN, Pin.IN, Pin.PULL_UP)
        except Exception as e:
            print(f"[SafetyMode] Mode switch failed: {e}")
            self.mode_switch = None

        # Fatigue detection state
        self.baseline_rms = None
        self.current_rms = 0.0
        self.fatigue_level = "normal"  # "normal", "warning", "critical"
        self.last_alert_time = 0
        self.alert_cooldown_ms = 300  # Prevent alert spam

        # Vibration state (for pattern timing)
        self.last_vibration_time = 0
        self.vibration_state = "idle"  # "idle", "warning", "critical"

        # Mode switch cooldown (prevent repeated toggles)
        self.last_mode_switch_time = 0
        self.mode_switch_cooldown_ms = 500  # Ignore inputs within 500ms

        # WiFi Manager (for PC dashboard)
        self.wifi = None
        if config.WIFI_ENABLED:
            try:
                self.wifi = WiFiManager()
                if config.DEBUG and config.DEBUG_CALIBRATION:
                    print("[SafetyMode] WiFi manager initialized")
            except Exception as e:
                print(f"[SafetyMode] WiFi manager failed: {e}")
                self.wifi = None

        print("[SafetyMode] Initialized (EMG=%s, LED=%s, Motor=%s, WiFi=%s)" %
              (config.ENABLE_EMG_SENSOR, config.ENABLE_LED, config.ENABLE_MOTOR, config.WIFI_ENABLED))

    def calibrate(self, duration_sec=60):
        """
        Baseline calibration: collect EMG data during rest
        Uses online RMS calculation to minimize memory usage

        Args:
            duration_sec: Calibration duration in seconds
        """
        if not config.ENABLE_EMG_SENSOR or not self.emg:
            print("[SafetyMode] EMG disabled - skipping calibration")
            return

        if config.DEBUG and config.DEBUG_CALIBRATION:
            print(f"[SafetyMode] Calibration starting ({duration_sec}s)...")

        if self.led:
            self.led.set_color("normal")  # Green during calibration

        # Online RMS calculation (no need to store all samples)
        sum_of_squares = 0.0
        sample_count = 0
        sample_rate = config.EMG_SAMPLE_RATE
        total_samples = sample_rate * duration_sec

        for i in range(total_samples):
            raw = self.emg.read_raw()
            # Accumulate sum of squares (memory efficient)
            sum_of_squares += raw * raw
            sample_count += 1

            if config.DEBUG and config.DEBUG_CALIBRATION:
                if (i + 1) % (sample_rate * 10) == 0:
                    print(f"  {(i + 1) // sample_rate}s...")

            time.sleep_us(1_000_000 // sample_rate)

        # Calculate baseline RMS from accumulated values
        if sample_count > 0:
            self.baseline_rms = (sum_of_squares / sample_count) ** 0.5
        else:
            self.baseline_rms = 0.0

        if config.DEBUG and config.DEBUG_CALIBRATION:
            print(f"[SafetyMode] Calibration complete. Baseline RMS: {self.baseline_rms:.0f}")
            print("[SafetyMode] Ready. Monitoring fatigue...")

    def _calculate_rms(self, samples):
        """
        Calculate RMS (Root Mean Square) of signal
        Optimized for memory efficiency
        """
        if not samples:
            return 0.0
        # Calculate RMS without storing intermediate values
        sum_sq = 0.0
        for s in samples:
            sum_sq += s * s
        return (sum_sq / len(samples)) ** 0.5

    def _calculate_fatigue_percentage(self):
        """
        Calculate fatigue percentage based on signal strength drop

        Returns:
            fatigue%: 0~100 (0% = full strength, 100% = completely fatigued)
        """
        if not self.baseline_rms or self.baseline_rms == 0:
            return 0.0

        # Signal drop = (baseline - current) / baseline * 100
        signal_drop = (self.baseline_rms - self.current_rms) / self.baseline_rms * 100
        # Clamp to 0~100%
        return max(0, min(100, signal_drop))

    def _update_fatigue_level(self):
        """Determine fatigue level from signal strength"""
        if self.baseline_rms is None:
            return

        # Calculate current signal strength as % of baseline
        signal_strength = (self.current_rms / self.baseline_rms) * 100

        # Determine level based on config thresholds
        if signal_strength >= config.EMG_NORMAL_THRESHOLD:
            self.fatigue_level = "normal"
        elif signal_strength >= config.EMG_WARNING_THRESHOLD:
            self.fatigue_level = "warning"
        else:
            self.fatigue_level = "critical"

    def _update_led_color(self):
        """Update LED based on fatigue level"""
        if not config.ENABLE_LED or not self.led:
            return

        colors = {
            "normal": "normal",
            "warning": "warning",
            "critical": "critical",
        }
        self.led.set_color(colors.get(self.fatigue_level, "normal"))

        if config.DEBUG and config.DEBUG_LED_CONTROL:
            print(f"[SafetyMode] LED: {self.fatigue_level}")

    def _update_motor_feedback(self):
        """
        Update vibration pattern based on fatigue level

        Patterns:
        - normal: Silent (no vibration)
        - warning: Short pulses with long interval
        - critical: Short pulses with short interval
        """
        if not config.ENABLE_MOTOR or not self.motor:
            return

        current_time = time.ticks_ms()
        time_since_last = time.ticks_diff(current_time, self.last_vibration_time)

        if self.fatigue_level == "normal":
            # Silent - no action
            self.motor.stop()
            self.vibration_state = "idle"

        elif self.fatigue_level == "warning":
            # Warning pattern: short pulse, long interval
            pulse_duration = config.VIBRATION_PULSE_DURATION
            interval = config.VIBRATION_INTERVAL_WARNING
            cycle_time = pulse_duration + interval

            if time_since_last >= cycle_time:
                # Start new cycle
                self.motor.single_pulse(
                    duration_ms=pulse_duration, intensity=config.MOTOR_WARNING_INTENSITY
                )
                self.last_vibration_time = current_time
                self.vibration_state = "warning"

                if config.DEBUG and config.DEBUG_MOTOR_CONTROL:
                    print(f"[SafetyMode] Motor: WARNING pulse")

        elif self.fatigue_level == "critical":
            # Critical pattern: short pulse, short interval (more urgent)
            pulse_duration = config.VIBRATION_PULSE_DURATION
            interval = config.VIBRATION_INTERVAL_CRITICAL
            cycle_time = pulse_duration + interval

            if time_since_last >= cycle_time:
                # Start new cycle
                self.motor.single_pulse(
                    duration_ms=pulse_duration,
                    intensity=config.MOTOR_CRITICAL_INTENSITY,
                )
                self.last_vibration_time = current_time
                self.vibration_state = "critical"

                if config.DEBUG and config.DEBUG_MOTOR_CONTROL:
                    print(f"[SafetyMode] Motor: CRITICAL pulse")

    def _print_status_log(self):
        """Print detailed status log for debugging"""
        if not (config.DEBUG and config.DEBUG_SAFETY_MODE):
            return

        fatigue_percent = self._calculate_fatigue_percentage()

        # LED color map
        color_map = {
            "normal": "🟢 GREEN",
            "warning": "🟡 YELLOW",
            "critical": "🔴 RED"
        }
        color = color_map.get(self.fatigue_level, "?")

        # Motor state
        motor_state = {
            "idle": "OFF",
            "warning": "PULSE(500ms)",
            "critical": "PULSE(200ms)"
        }.get(self.vibration_state, "?")

        print(f"[SafetyMode] RMS: {self.current_rms:6.0f} | "
              f"Fatigue: {fatigue_percent:5.1f}% | "
              f"Level: {self.fatigue_level:8s} | "
              f"LED: {color:12s} | "
              f"Motor: {motor_state}")

    def update(self, chunk_size=None):
        """
        Process one cycle of fatigue monitoring
        Uses online RMS calculation to minimize memory usage

        Args:
            chunk_size: Number of samples to process (default: config.EMG_CHUNK_SIZE)

        Returns:
            dict: Current status (fatigue_level, fatigue_percent, rms)
        """
        if not config.ENABLE_EMG_SENSOR or not self.emg:
            return {
                "mode": "safety",
                "error": True,
                "message": "EMG sensor disabled",
            }

        if chunk_size is None:
            chunk_size = config.EMG_CHUNK_SIZE

        # Collect and calculate RMS online (no temporary storage)
        sum_of_squares = 0.0
        interval_us = 1_000_000 // config.EMG_SAMPLE_RATE

        for i in range(chunk_size):
            raw = self.emg.read_raw()
            sum_of_squares += raw * raw
            time.sleep_us(interval_us)

        # Calculate RMS from accumulated values
        self.current_rms = (sum_of_squares / chunk_size) ** 0.5

        # Update fatigue level
        self._update_fatigue_level()

        # Update LED and motor feedback
        self._update_led_color()
        self._update_motor_feedback()

        # Detailed debug output
        self._print_status_log()

        # Send data to PC dashboard via WiFi
        if self.wifi:
            self.wifi.send_safety_mode_data(
                rms=self.current_rms,
                fatigue_pct=self._calculate_fatigue_percentage(),
                level=self.fatigue_level,
                baseline_rms=self.baseline_rms,
            )

        return {
            "mode": "safety",
            "fatigue_level": self.fatigue_level,
            "fatigue_percent": self._calculate_fatigue_percentage(),
            "rms": self.current_rms,
            "baseline_rms": self.baseline_rms,
        }

    def check_mode_switch(self):
        """
        Check if mode switch was pressed
        Uses cooldown to prevent repeated toggles

        Returns:
            True if button pressed and cooldown elapsed
        """
        if not self.mode_switch:
            return False

        # Check if button is pressed (HIGH = 1)
        if self.mode_switch.value() == 1:
            current_time = time.ticks_ms()
            time_since_last = time.ticks_diff(current_time, self.last_mode_switch_time)

            # Only register if cooldown has passed (500ms)
            if time_since_last > self.mode_switch_cooldown_ms:
                self.last_mode_switch_time = current_time
                return True

        return False

    def cleanup(self):
        """Stop all feedback and reset state"""
        if config.ENABLE_MOTOR and self.motor:
            self.motor.stop()
        if config.ENABLE_LED and self.led:
            self.led.off()
        print("[SafetyMode] Cleanup complete")


def safety_mode_loop(duration_sec=None):
    """
    Main Safety Mode loop

    Args:
        duration_sec: Run for N seconds (None = infinite, until mode switch)
    """
    mode = SafetyMode()

    # Calibration phase
    calibrate_duration = config.CALIBRATION_DURATION_SEC
    if config.DEBUG:
        print(f"[SafetyMode] Calibration will take {calibrate_duration} seconds...")
        print("[SafetyMode] Keep arm relaxed during calibration")

    mode.calibrate(duration_sec=calibrate_duration)

    # Monitoring phase
    print("[SafetyMode] Entering monitoring phase...")
    start_time = time.time()

    try:
        iteration = 0
        while True:
            iteration += 1

            # Check mode switch with debounce
            if mode.check_mode_switch():
                print("\n" + "=" * 70)
                print("[SafetyMode] 🔘 MODE SWITCH DETECTED!")
                print("=" * 70)
                print("[SafetyMode] Transitioning to Control Mode...")
                mode.cleanup()
                return "control"

            # Update fatigue monitoring
            status = mode.update()

            # Check duration limit
            if duration_sec and (time.time() - start_time) > duration_sec:
                print("[SafetyMode] Duration limit reached")
                mode.cleanup()
                return "stop"

            # Sleep briefly to prevent CPU saturation
            time.sleep_ms(100)

    except KeyboardInterrupt:
        print("[SafetyMode] Interrupted by user")
        mode.cleanup()
        return "stop"
