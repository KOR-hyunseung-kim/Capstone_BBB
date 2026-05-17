"""
EMG Signal Processing & Fatigue Detection for BBB Safety Mode
- Calibration: 1 minute baseline establishment
- Fatigue detection: RMS-based threshold judgment
- Modular design: Ready for Control Mode integration later

Note: MicroPython compatible (no typing module)
"""

import time
import math


class EMGProcessor:
    """
    EMG signal processing engine for fatigue monitoring
    - Uses RMS (Root Mean Square) as muscle fatigue indicator
    - Baseline calibration required before safety monitoring
    """

    def __init__(self, emg_sensor, vibrator, sample_rate=1000, chunk_size=1000):
        """
        Initialize EMG processor

        Args:
            emg_sensor: EMGSensor instance (firmware.sensor.emg.EMGSensor)
            vibrator: VibratorMotor instance (firmware.ui.motor.VibratorMotor)
            sample_rate: Sampling rate in Hz (default 1000)
            chunk_size: Samples per processing chunk (default 1000 = 1 second)
        """
        self.emg_sensor = emg_sensor
        self.vibrator = vibrator
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        # Calibration baseline
        self.baseline_rms = None
        # Note: Don't store all samples (memory limited on ESP32)
        # Instead, calculate RMS per chunk and average them

        # Fatigue thresholds (percentage of baseline RMS)
        # Signal strength: higher = less fatigue
        self.critical_threshold = 90  # % - Normal threshold (>= 90%)
        self.warning_threshold = 70  # % - Warning threshold (70-90%, < 70% is critical)

        # Mode state
        self.current_mode = "idle"  # idle, calibrating, monitoring
        self.last_fatigue_level = "normal"

    def _calculate_rms(self, samples):
        """
        Calculate RMS (Root Mean Square) of signal

        Args:
            samples: List of raw ADC values

        Returns:
            RMS value (float)
        """
        if not samples:
            return 0.0

        sum_sq = sum(x * x for x in samples)
        return math.sqrt(sum_sq / len(samples))

    def _collect_chunk(self):
        """
        Collect one chunk of EMG samples

        Returns:
            List of ADC samples
        """
        return self.emg_sensor.sample_chunk(self.chunk_size)

    def calibrate(self, duration_sec=60, oled_display=None):
        """
        Perform calibration: collect baseline EMG during rest period

        Memory-efficient version (streaming):
        1. Collect chunks for duration_sec
        2. Calculate RMS for each chunk
        3. Average all chunk RMS values as baseline
        (Don't store all samples - ESP32 has limited RAM)

        Args:
            duration_sec: Calibration duration in seconds (default 60)
            oled_display: Optional OLEDDisplay for progress feedback

        Returns:
            True if successful, False otherwise
        """
        self.current_mode = "calibrating"
        print(f"[EMG] Calibration start - collecting {duration_sec}s baseline")

        if oled_display:
            oled_display.show_message("Calibrating...", "Please RELAX", "your arm")

        n_chunks = max(1, (duration_sec * self.sample_rate) // self.chunk_size)
        rms_values = []  # Store RMS per chunk (not raw samples)

        for i in range(n_chunks):
            chunk = self._collect_chunk()
            if chunk:
                chunk_rms = self._calculate_rms(chunk)
                rms_values.append(chunk_rms)

            progress = int((i + 1) * 100 / n_chunks)
            print(f"[EMG] Calibration {progress}%")

            # Update OLED with progress
            if oled_display:
                oled_display.show_progress("Calibrating", progress)

        if not rms_values:
            print("[EMG] Calibration failed: no samples collected")
            if oled_display:
                oled_display.show_message("Calibration", "FAILED!", "No samples")
            return False

        # Average RMS across all chunks as baseline
        self.baseline_rms = sum(rms_values) / len(rms_values)
        print(f"[EMG] Calibration complete - baseline RMS: {self.baseline_rms:.1f}")

        if oled_display:
            oled_display.show_message("Calibration", "Complete!", f"BL:{self.baseline_rms:.0f}")
            import time
            time.sleep(1)

        self.current_mode = "monitoring"
        return True

    def get_fatigue_level(self, rms):
        """
        Determine fatigue level based on current RMS vs baseline

        Signal strength determines fatigue: higher RMS = less fatigue
        - >= 90% of baseline: normal (fresh muscle)
        - 70-90% of baseline: warning (moderate fatigue)
        - < 70% of baseline: critical (severe fatigue)

        Args:
            rms: Current RMS value

        Returns:
            Tuple of (level, percentage):
            - level: "normal", "warning", "critical"
            - percentage: ratio of current RMS to baseline (0-100%)
        """
        if not self.baseline_rms or self.baseline_rms == 0:
            return "normal", 100.0

        signal_pct = (rms / self.baseline_rms) * 100

        if signal_pct >= self.critical_threshold:  # >= 90%
            level = "normal"
        elif signal_pct >= self.warning_threshold:  # >= 70%
            level = "warning"
        else:  # < 70%
            level = "critical"

        return level, signal_pct

    def update_with_feedback(self, rms):
        """
        Monitor EMG, update fatigue level, and trigger haptic feedback

        Args:
            rms: Current RMS value from sensor

        Returns:
            Fatigue level string ("normal", "warning", "critical")
        """
        level, fatigue_pct = self.get_fatigue_level(rms)

        # Only vibrate if level changed (and vibrator is available)
        if self.vibrator is not None and level != self.last_fatigue_level:
            if level == "warning":
                self.vibrator.alert_pattern("warning")
            elif level == "critical":
                self.vibrator.alert_pattern("critical")

        self.last_fatigue_level = level
        return level

    def run_monitoring_cycle(self):
        """
        Single monitoring cycle: collect chunk, calculate RMS, detect fatigue

        Returns:
            Tuple of (rms, level):
            - rms: Current RMS value
            - level: Fatigue level ("normal", "warning", "critical")
        """
        if self.current_mode != "monitoring" or not self.baseline_rms:
            return 0.0, "normal"

        chunk = self._collect_chunk()
        rms = self._calculate_rms(chunk)
        level = self.update_with_feedback(rms)

        return rms, level

    def get_stats(self):
        """
        Get current processor state (for debugging/logging)

        Returns:
            Dictionary with baseline_rms, current mode, thresholds
        """
        return {
            "baseline_rms": self.baseline_rms,
            "mode": self.current_mode,
            "warning_threshold_pct": self.warning_threshold,
            "critical_threshold_pct": self.critical_threshold,
        }

    def reset(self):
        """Reset calibration and return to idle state"""
        self.baseline_rms = None
        self.current_mode = "idle"
        self.last_fatigue_level = "normal"


class SafetyModeController:
    """
    Coordinator for Safety Mode operation
    - Manages calibration and monitoring loop
    - Controls LED and OLED display for user feedback
    - Ready to share processor with Control Mode later
    """

    def __init__(self, emg_processor, led_controller=None, oled_display=None):
        """
        Initialize Safety Mode controller

        Args:
            emg_processor: EMGProcessor instance
            led_controller: Optional RGBLEDController for visual feedback
            oled_display: Optional OLEDDisplay for status display
        """
        self.processor = emg_processor
        self.led = led_controller
        self.oled = oled_display
        self.running = False
        self.monitoring_interval_ms = 1000  # Monitor every 1 second

    def run_once(self, current_rms=None):
        """
        Execute one monitoring cycle with LED and OLED updates

        Args:
            current_rms: Optional RMS for display (calculated if not provided)

        Returns:
            Tuple of (rms, fatigue_level)
        """
        rms, level = self.processor.run_monitoring_cycle()

        # Update visual feedback
        if self.led:
            self._update_led(level)

        if self.oled:
            self._update_oled(rms, level)

        return rms, level

    def _update_led(self, level):
        """Update RGB LED based on fatigue level"""
        if not self.led:
            return

        # RGBLEDController.set_color() takes level string directly
        self.led.set_color(level)

    def _update_oled(self, rms, level):
        """Update OLED display with EMG status"""
        if not self.oled or not self.processor.baseline_rms:
            return

        # Calculate fatigue percentage
        signal_pct = (rms / self.processor.baseline_rms) * 100

        # Prepare display data
        display_data = {
            "fatigue_pct": signal_pct,
            "mf": 0.0,  # Placeholder for Median Frequency (future)
            "level": level,
        }

        self.oled.update(display_data)

    def start(self, duration_sec=60):
        """
        Start Safety Mode (calibration -> continuous monitoring)

        Args:
            duration_sec: Calibration duration

        Returns:
            True if calibration succeeded
        """
        print("[Safety] Starting Safety Mode...")

        if not self.processor.calibrate(duration_sec, oled_display=self.oled):
            print("[Safety] Calibration failed")
            return False

        print("[Safety] Calibration done, entering monitoring loop")
        self.running = True
        return True

    def stop(self):
        """Stop monitoring and cleanup"""
        self.running = False
        self.processor.reset()
        print("[Safety] Safety Mode stopped")
