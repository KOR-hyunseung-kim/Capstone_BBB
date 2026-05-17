"""
BBB Control Mode Main Loop
IMU 기울기 → 마우스 커서 이동 + EMG → 클릭

Usage:
    Enable in config.py: CONTROL_MODE_ENABLED = True
    Then run: import control_main; control_main.main()
"""

import time
import math
from machine import Pin

# Import drivers
from sensor.icm20602 import ICM20602
from sensor.emg import EMGSensor
from ui.motor import VibratorMotor
from ui.led import RGBLed
from ui.oled import OLEDDisplay

# Import algorithm
from algo.control import (
    CursorController,
    EMGClickDetector,
    ModeSwitch,
    SimpleSmoother,
)

# Import config
try:
    from config import (
        PIN_IMU_SDA,
        PIN_IMU_SCL,
        PIN_EMG,
        PIN_MOTOR,
        PIN_LED_R,
        PIN_LED_G,
        PIN_LED_B,
        PIN_MODE_SWITCH,
    )
except ImportError:
    # Default pins
    PIN_IMU_SDA = 8
    PIN_IMU_SCL = 9
    PIN_EMG = 35
    PIN_MOTOR = 5
    PIN_LED_R = 2
    PIN_LED_G = 3
    PIN_LED_B = 4
    PIN_MODE_SWITCH = 6


class ControlMode:
    """Control Mode 메인 로직."""

    def __init__(self, screen_width=1920, screen_height=1080):
        """초기화."""
        print("\n" + "=" * 70)
        print("BBB CONTROL MODE - IMU 마우스 제어")
        print("=" * 70)

        self.screen_width = screen_width
        self.screen_height = screen_height

        # 센서 초기화
        print("\n[1] 센서 초기화...")
        try:
            self.imu = ICM20602(sda_pin=PIN_IMU_SDA, scl_pin=PIN_IMU_SCL)
            print("[OK] IMU 초기화")
        except Exception as e:
            print(f"[ERROR] IMU 실패: {e}")
            raise

        try:
            self.emg = EMGSensor(pin=PIN_EMG)
            print("[OK] EMG 초기화")
        except Exception as e:
            print(f"[ERROR] EMG 실패: {e}")
            self.emg = None

        # UI 초기화
        print("\n[2] UI 초기화...")
        try:
            self.motor = VibratorMotor(pin=PIN_MOTOR)
            print("[OK] 진동모터 초기화")
        except Exception as e:
            print(f"[ERROR] 진동모터 실패: {e}")
            self.motor = None

        try:
            self.led = RGBLed(
                pin_r=PIN_LED_R,
                pin_g=PIN_LED_G,
                pin_b=PIN_LED_B,
            )
            self.led.set_color("cyan")  # 컨트롤 모드 = 시안색
            print("[OK] RGB LED 초기화")
        except Exception as e:
            print(f"[ERROR] LED 실패: {e}")
            self.led = None

        try:
            self.oled = OLEDDisplay()
            self.oled.display_text("Control Mode")
            print("[OK] OLED 초기화")
        except Exception as e:
            print(f"[ERROR] OLED 실패: {e}")
            self.oled = None

        # 제어 로직 초기화
        print("\n[3] 제어 로직 초기화...")
        self.cursor = CursorController(
            screen_width=screen_width,
            screen_height=screen_height,
            sensitivity=1.5,  # 감도 조정 가능
        )
        self.emg_detector = EMGClickDetector(threshold=0.6)
        self.mode_switch = ModeSwitch(debounce_time=200)

        # 상태
        self.is_calibrated = False
        self.calibration_samples = 0

        print("\n[4] 캘리브레이션 준비 중...")
        self.calibration_samples_needed = 50

    def calibrate(self):
        """
        캘리브레이션: 기준 기울기 설정.
        기기를 수평으로 놓고 기다리세요.
        """
        print("\n" + "=" * 70)
        print("CALIBRATION: 기기를 수평으로 놓고 대기하세요")
        print("=" * 70)

        if self.oled:
            self.oled.clear()
            self.oled.display_text("Calibrating...")

        ax_samples = []
        ay_samples = []

        for i in range(self.calibration_samples_needed):
            try:
                ax, ay, az = self.imu.get_accel()  # Raw 값
                ax_samples.append(ax)
                ay_samples.append(ay)

                if i % 10 == 0:
                    progress = int(i / self.calibration_samples_needed * 100)
                    print(f"  [{progress}%] Sample {i}")
                    if self.oled:
                        self.oled.display_text(f"Cal: {progress}%")

                time.sleep(0.02)  # 50Hz

            except Exception as e:
                print(f"[ERROR] 샘플 수집 실패: {e}")

        # 교정
        self.cursor.calibrate(ax_samples, ay_samples)
        self.is_calibrated = True

        print("[OK] 캘리브레이션 완료!")
        if self.oled:
            self.oled.clear()
            self.oled.display_text("Ready!")

        # 진동 피드백
        if self.motor:
            self.motor.vibrate(intensity=50, duration=200)

    def run(self, duration=0):
        """
        메인 루프 실행.

        Args:
            duration: 실행 시간 (초), 0 = 무한
        """
        if not self.is_calibrated:
            self.calibrate()

        print("\n" + "=" * 70)
        print("CONTROL MODE RUNNING")
        print("=" * 70)
        print("기울기로 커서 이동 | EMG로 클릭 | 택트 스위치로 모드 전환")
        print("-" * 70)

        start_time = time.time()
        frame_count = 0

        try:
            while True:
                frame_start = time.time()

                # 센서 읽기
                ax, ay, az = self.imu.get_accel()  # Raw 값 사용!

                # EMG 읽기 (있으면)
                emg_level = 0.0
                if self.emg:
                    try:
                        emg_raw = self.emg.read()
                        emg_level = emg_raw / 4095.0  # 정규화 (0~1)
                    except Exception:
                        pass

                # 커서 이동
                delta_x, delta_y = self.cursor.get_cursor_delta(ax, ay)
                if delta_x != 0 or delta_y != 0:
                    self.cursor.update_position(delta_x, delta_y)

                # 클릭 감지
                current_time = int(frame_start * 1000) % (2**31)
                click = self.emg_detector.update(emg_level, current_time)

                if click:
                    print(
                        f"[CLICK] EMG={emg_level:.2f}, "
                        f"Cursor=({self.cursor.cursor_x}, "
                        f"{self.cursor.cursor_y})"
                    )
                    if self.motor:
                        self.motor.vibrate(intensity=100, duration=100)

                # OLED 표시 (10Hz)
                if frame_count % 5 == 0:
                    if self.oled:
                        line1 = f"X:{ax:5.1f} Y:{ay:5.1f}"
                        line2 = (
                            f"Pos:({self.cursor.cursor_x:4d},"
                            f"{self.cursor.cursor_y:4d})"
                        )
                        line3 = f"EMG:{emg_level:.2f} "
                        if self.emg_detector.is_clicking():
                            line3 += "[CLICK]"

                        self.oled.clear()
                        self.oled.display_text(line1)
                        self.oled.display_text(line2)
                        self.oled.display_text(line3)

                # 모드 전환 확인 (택트 스위치)
                # TODO: GPIO 읽기 추가

                frame_count += 1

                # 지속 시간 확인
                if duration > 0:
                    if time.time() - start_time > duration:
                        break

                # 프레임 레이트 유지 (50Hz)
                frame_time = time.time() - frame_start
                sleep_time = 0.02 - frame_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n사용자 중단")
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback

            try:
                traceback.print_exc()
            except:
                pass

        # 정리
        print("\n" + "=" * 70)
        print(f"Control Mode 종료 ({frame_count} frames)")
        print("=" * 70)

        if self.led:
            self.led.set_color("off")
        if self.oled:
            self.oled.clear()


def main():
    """메인 함수."""
    try:
        control = ControlMode(screen_width=1920, screen_height=1080)
        control.run(duration=300)  # 5분 실행
    except Exception as e:
        print(f"\n[FATAL] {e}")
        try:
            import traceback

            traceback.print_exc()
        except:
            pass


if __name__ == "__main__":
    main()
