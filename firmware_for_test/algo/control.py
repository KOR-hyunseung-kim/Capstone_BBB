"""
Control Mode: IMU 기울기 → 마우스 커서 이동 변환
Raw 가속도 값 사용 (빠른 반응성)
약간의 이동평균 필터만 적용 (안정성)
"""

import math


class SimpleSmoother:
    """경량 이동평균 필터 (Raw 값의 반응성 유지)."""

    def __init__(self, window_size=3):
        """
        Args:
            window_size: 평균값 계산 윈도우 (기본 3)
        """
        self.window_size = window_size
        self.values = []

    def update(self, value):
        """새로운 값 추가 후 평균 반환."""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
        return sum(self.values) / len(self.values)

    def reset(self):
        """초기화."""
        self.values = []


class CursorController:
    """IMU 기울기 → 마우스 커서 이동 제어기."""

    def __init__(self, screen_width=1920, screen_height=1080, sensitivity=1.0):
        """
        Initialize cursor controller.

        Args:
            screen_width: 화면 너비 (픽셀)
            screen_height: 화면 높이 (픽셀)
            sensitivity: 감도 (1.0 = 기본)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sensitivity = sensitivity

        # 이동평균 필터 (Raw 값의 반응성 유지)
        self.smoother_x = SimpleSmoother(window_size=2)
        self.smoother_y = SimpleSmoother(window_size=2)

        # 기준점 (calibration)
        self.center_pitch = 0.0
        self.center_roll = 0.0

        # 현재 커서 위치
        self.cursor_x = screen_width // 2
        self.cursor_y = screen_height // 2

        print(f"[Init] Cursor Controller: {screen_width}x{screen_height}")
        print(f"[Init] Sensitivity: {sensitivity}x")

    def calibrate(self, ax_samples, ay_samples):
        """
        교정 (30~50개 샘플 평균).

        Args:
            ax_samples: 가속도 X 샘플 리스트
            ay_samples: 가속도 Y 샘플 리스트
        """
        if not ax_samples or not ay_samples:
            print("[WARN] Empty samples for calibration")
            return

        # 피치/롤 계산 (Raw 값 사용)
        pitches = []
        rolls = []

        for ax, ay in zip(ax_samples, ay_samples):
            pitch = math.degrees(
                math.atan2(ax, 9.81)
            )
            roll = math.degrees(
                math.atan2(ay, 9.81)
            )
            pitches.append(pitch)
            rolls.append(roll)

        self.center_pitch = sum(pitches) / len(pitches)
        self.center_roll = sum(rolls) / len(rolls)

        print(
            f"[OK] Calibration: "
            f"center_pitch={self.center_pitch:.1f}°, "
            f"center_roll={self.center_roll:.1f}°"
        )

    def get_cursor_delta(self, ax, ay):
        """
        가속도 → 커서 이동량 변환.

        Args:
            ax: X축 가속도 (m/s², Raw 값)
            ay: Y축 가속도 (m/s², Raw 값)

        Returns:
            (delta_x, delta_y): 커서 이동량 (픽셀)
        """
        # 피치/롤 계산 (Raw 값, 빠른 반응)
        pitch = math.degrees(math.atan2(ax, 9.81))
        roll = math.degrees(math.atan2(ay, 9.81))

        # 기준점으로부터 변위
        delta_pitch = pitch - self.center_pitch
        delta_roll = roll - self.center_roll

        # 약간의 smoothing (window=2)
        delta_pitch = self.smoother_x.update(delta_pitch)
        delta_roll = self.smoother_y.update(delta_roll)

        # 픽셀로 변환 (감도 조정)
        # 1도 = 대략 10 픽셀 (조정 가능)
        pixels_per_degree = 10 * self.sensitivity

        cursor_delta_x = int(delta_roll * pixels_per_degree)
        cursor_delta_y = int(-delta_pitch * pixels_per_degree)  # Y 반전

        return cursor_delta_x, cursor_delta_y

    def update_position(self, delta_x, delta_y):
        """
        커서 위치 업데이트 (화면 경계 확인).

        Args:
            delta_x: X 이동량
            delta_y: Y 이동량

        Returns:
            (cursor_x, cursor_y): 새로운 커서 위치
        """
        self.cursor_x += delta_x
        self.cursor_y += delta_y

        # 화면 경계 확인
        self.cursor_x = max(0, min(self.cursor_x, self.screen_width - 1))
        self.cursor_y = max(0, min(self.cursor_y, self.screen_height - 1))

        return self.cursor_x, self.cursor_y

    def reset(self):
        """필터 및 커서 초기화."""
        self.smoother_x.reset()
        self.smoother_y.reset()
        self.cursor_x = self.screen_width // 2
        self.cursor_y = self.screen_height // 2


class EMGClickDetector:
    """EMG 신호에서 주먹 쥐기(클릭) 감지."""

    def __init__(self, threshold=0.7, hold_time=100):
        """
        Initialize click detector.

        Args:
            threshold: EMG 신호 임계값 (0.0~1.0)
            hold_time: 클릭 유지 시간 (ms)
        """
        self.threshold = threshold
        self.hold_time = hold_time
        self.click_active = False
        self.click_start_time = 0

    def update(self, emg_level, current_time):
        """
        EMG 신호 업데이트 (0.0~1.0).

        Args:
            emg_level: 정규화된 EMG 신호 (0.0~1.0)
            current_time: 현재 시간 (ms)

        Returns:
            click_event: True if 클릭 발생, False otherwise
        """
        click_event = False

        if emg_level > self.threshold:
            if not self.click_active:
                # 새로운 클릭 시작
                self.click_active = True
                self.click_start_time = current_time
                click_event = True
        else:
            if self.click_active:
                # 클릭 종료
                self.click_active = False

        return click_event

    def is_clicking(self):
        """현재 클릭 중인가?"""
        return self.click_active


class ModeSwitch:
    """Safety ↔ Control 모드 전환 (택트 스위치)."""

    def __init__(self, debounce_time=50):
        """
        Args:
            debounce_time: 디바운싱 시간 (ms)
        """
        self.debounce_time = debounce_time
        self.last_toggle_time = 0
        self.current_mode = "safety"  # safety, control

    def toggle(self, current_time):
        """
        모드 전환 시도.

        Args:
            current_time: 현재 시간 (ms)

        Returns:
            new_mode: 새로운 모드 ('safety' or 'control')
            success: 전환 성공 여부
        """
        if current_time - self.last_toggle_time < self.debounce_time:
            return self.current_mode, False

        self.last_toggle_time = current_time

        if self.current_mode == "safety":
            self.current_mode = "control"
        else:
            self.current_mode = "safety"

        return self.current_mode, True

    def get_mode(self):
        """현재 모드 반환."""
        return self.current_mode
