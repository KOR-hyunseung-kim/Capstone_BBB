"""
BBB Hardware Configuration & Pin Definitions
Centralized configuration for easy modification
"""

# ============================================================================
# GPIO Pin Assignments
# ============================================================================

# Sensor Input
EMG_ADC_PIN = 1  # GPIO1 - MyoWare 2.0 analog output

# Output Control
VIBRATOR_PIN = 38  # GPIO38 - Vibration motor (PWM)
LED_RED_PIN = 18  # GPIO18 - RGB LED red channel (PWM)
LED_GREEN_PIN = 17  # GPIO17 - RGB LED green channel (PWM)
LED_BLUE_PIN = 8  # GPIO8 - RGB LED blue channel (PWM)

# Optional: Mode Switch
MODE_SWITCH_PIN = 21  # GPIO21 for Safety/Control mode toggle

# ============================================================================
# I2C Configuration (for OLED & IMU)
# ============================================================================

# OLED Pin Mapping: VDD(3.3V) → VCC, GND → GND, SCK → GPIO10, SDA → GPIO9
I2C_SDA_PIN = 9  # GPIO9 - I2C SDA (OLED SDA pin)
I2C_SCL_PIN = 10  # GPIO10 - I2C SCL / SCK (OLED SCK pin)
I2C_FREQUENCY = 100_000  # 100kHz (낮추면 안정적, OLED 호환성 증가)

# I2C Slave Addresses
OLED_I2C_ADDR = 0x3C  # SSD1306 OLED (128x64)
IMU_I2C_ADDR = 0x68  # MPU6050 IMU

# ============================================================================
# EMG Signal Processing Parameters
# ============================================================================

EMG_SAMPLE_RATE = 1000  # Hz - ADC sampling rate
EMG_CHUNK_SIZE = 1000  # samples - Processing window (1 second)

# Fatigue Detection Thresholds (% of baseline RMS)
# Higher signal strength = less fatigue
EMG_NORMAL_THRESHOLD = 90  # >= 90% baseline = normal (green)
EMG_WARNING_THRESHOLD = 70  # 70-90% baseline = warning (yellow)
# < 70% baseline = critical (red)

# ============================================================================
# Vibration Motor Feedback
# ============================================================================

MOTOR_PWM_FREQUENCY = 100  # Hz
MOTOR_WARNING_INTENSITY = 800  # PWM duty (0~1023) - medium vibration
MOTOR_CRITICAL_INTENSITY = 1000  # PWM duty (0~1023) - strong vibration
MOTOR_ALERT_DURATION_MS = 100  # Pulse duration in ms

# ============================================================================
# OLED Display Configuration
# ============================================================================

OLED_WIDTH = 128  # pixels
OLED_HEIGHT = 64  # pixels
OLED_I2C_UPDATE_RATE = 100  # ms - screen refresh interval

# ============================================================================
# Calibration Settings
# ============================================================================

# Calibration duration in seconds
# Memory-efficient online RMS calculation (no sample buffering)
# Recommended for ESP32-S3:
#   - 10-15 seconds (quick, memory-safe)
#   - 20-30 seconds (standard)
#   - 60 seconds (accurate, if memory allows)
CALIBRATION_DURATION_SEC = 15  # 메모리 부족 방지 (10~30초 권장)

# ============================================================================
# WiFi Configuration
# ============================================================================

WIFI_ENABLED = True  # Enable WiFi UDP communication

# WiFi Network Settings
WIFI_SSID = "SK_WiFiGIGAE19E_2.4G"  # Change to your WiFi network name
WIFI_PASSWORD = "@urhome0812"  # Change to your WiFi password

# PC Receiver Settings (where UDP data is sent)
PC_IP = "192.168.45.115"  # Change to your PC IP address (check with: ipconfig)
PC_PORT = 5005  # UDP port (match with receiver script)

# WiFi Connection Timeout
WIFI_CONNECT_TIMEOUT = 10  # seconds

# ============================================================================
# Debug & Device Control
# ============================================================================

DEBUG = True  # Enable debug prints and detailed logging

# Device Enable/Disable (for testing without all hardware)
ENABLE_EMG_SENSOR = True  # Read EMG sensor
ENABLE_IMU_SENSOR = True  # Read IMU sensor (MPU6050)
ENABLE_MOTOR = True  # Control vibration motor
ENABLE_LED = True  # Control RGB LED
ENABLE_OLED = True  # Display on OLED screen (optional)

# Mode-specific Debug Options
DEBUG_SAFETY_MODE = True  # Enable detailed debug for Safety Mode
DEBUG_CONTROL_MODE = True  # Enable detailed debug for Control Mode

# Detailed Debug Output Options
DEBUG_EMG_VALUES = True  # Print EMG RMS values every cycle
DEBUG_LED_CONTROL = True  # Print LED color changes
DEBUG_MOTOR_CONTROL = True  # Print motor control signals
DEBUG_IMU_VALUES = True  # Print IMU accelerometer/gyro values
DEBUG_CALIBRATION = True  # Print calibration progress
DEBUG_INTERVAL_CYCLES = 1  # Print debug info every N cycles (1 = every cycle, 10 = every 10 cycles)

# ============================================================================
# Port & Communication Configuration
# ============================================================================

# I2C Port Selection (default: I2C(0) on ESP32-S3)
I2C_PORT = 0  # I2C port number (0 or 1 for ESP32-S3)

# Serial Communication (for Thonny debugging)
UART_ENABLED = True  # Enable UART debug output
UART_BAUD = 115200  # UART baud rate

# ============================================================================
# Advanced Configuration
# ============================================================================

# IMU Sensor Type (Control Mode)
# Options: "MPU6050" or "ICM20602"
IMU_TYPE = "ICM20602"  # Change to "MPU6050" if using that model instead

# Complementary Filter Alpha (Control Mode)
COMPLEMENTARY_FILTER_ALPHA = 0.98  # Weight for gyroscope (0.95~0.99)
COMPLEMENTARY_FILTER_DT = 0.01  # Time delta in seconds (10ms for 100Hz sampling)

# ============================================================================
# Cursor Control Speed (Control Mode) - Dynamic Speed Based on Tilt Angle
# ============================================================================

# Minimum tilt angle to register movement (deadzone)
CURSOR_DEADZONE = 2.0  # Degrees (tilt below this is ignored)

# Speed range for dynamic cursor control
CURSOR_SPEED_MIN = 5      # Pixels per degree (slow movement at small tilt)
CURSOR_SPEED_MAX = 50     # Pixels per degree (fast movement at large tilt)

# Tilt angle at which maximum speed is reached
CURSOR_MAX_TILT = 30.0    # Degrees (tilt >= this reaches CURSOR_SPEED_MAX)

# Cursor bounds (0~1024 range, center at 512)
CURSOR_X_MIN = 0
CURSOR_X_MAX = 1024
CURSOR_Y_MIN = 0
CURSOR_Y_MAX = 1024
CURSOR_CENTER_X = 512
CURSOR_CENTER_Y = 512

# EMG Spike Detection Threshold (Control Mode)
EMG_SPIKE_THRESHOLD = 3500  # ADC value threshold for click detection

# Safety Mode Vibration Timing
VIBRATION_PULSE_DURATION = 100  # Duration of single vibration pulse (ms)
VIBRATION_INTERVAL_WARNING = 500  # Interval between pulses in warning mode (ms)
VIBRATION_INTERVAL_CRITICAL = 200  # Interval between pulses in critical mode (ms)


