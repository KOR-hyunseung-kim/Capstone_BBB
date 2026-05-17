# Config, LED, OLED 통합 및 임계값 최적화

**날짜**: 2026-05-06 (추가 작업)
**작업자**: Claude Code (fw-developer agent)
**관련 파일**:
- `firmware/config.py` (NEW)
- `firmware/algo/emg_processor.py` (수정)
- `firmware/main.py` (전체 재작성)
- `tests/test_emg_fatigue.py` (테스트 업데이트)

## 요약

핀맵을 상수 파일로 중앙집중화하고, Safety Mode에 RGB LED와 OLED 디스플레이 피드백을 추가했습니다. 임계값도 사용자 경험 중심으로 재설정했습니다.

## 주요 변경 사항

### 1. 핀맵 중앙화 (`firmware/config.py`)

모든 GPIO 핀 번호와 설정값을 한곳에 정의하여 유지보수 용이성 향상:

```python
# 센서 입력
EMG_ADC_PIN = 1  # GPIO1 - MyoWare 2.0

# 출력 제어
VIBRATOR_PIN = 38  # GPIO38 - 진동모터
LED_RED_PIN = 17  # RGB LED 빨간색
LED_GREEN_PIN = 18  # RGB LED 녹색
LED_BLUE_PIN = 19  # RGB LED 파란색

# I2C (OLED, IMU)
I2C_SDA_PIN = 8  # GPIO8
I2C_SCL_PIN = 9  # GPIO9

# DSP 파라미터
EMG_NORMAL_THRESHOLD = 90  # 정상: ≥90%
EMG_WARNING_THRESHOLD = 70  # 주의: 70~90%, 경고: <70%

# 진동모터 강도
MOTOR_WARNING_INTENSITY = 800  # 주의 - 약한 진동
MOTOR_CRITICAL_INTENSITY = 1000  # 경고 - 강한 진동
```

**장점**:
- 나중에 핀 변경 시 config.py 한 파일만 수정
- 모든 모듈에서 일관된 설정값 사용
- H/W 프로토타입 변경 시 빠른 적응

### 2. 임계값 재설정 (더 관대한 기준)

**이전**: >= 95% (정상) | 80~95% (주의) | < 80% (경고)
**현재**: >= 90% (정상) | 70~90% (주의) | < 70% (경고)

**변경 이유**:
- 실제 피로도 감지 기준을 현실적으로 조정
- 70% 이상에서만 경고 → 오알람 감소
- 사용자 운동 능력 개인차 고려

| 신호 강도 | 상태 | LED 색상 | 진동 강도 |
|-----------|------|---------|---------|
| ≥ 90% | ✓ 정상 | 🟢 초록 | 없음 |
| 70~90% | ⚠️ 주의 | 🟡 주황 | 약함(800) |
| < 70% | 🚨 경고 | 🔴 빨강 | 강함(1000) |

### 3. SafetyModeController 확장

LED와 OLED 제어 기능 추가:

```python
class SafetyModeController:
    def __init__(self, emg_processor, led_controller=None, oled_display=None):
        # ...
        
    def run_once(self):
        rms, level = self.processor.run_monitoring_cycle()
        self._update_led(level)        # RGB LED 업데이트
        self._update_oled(rms, level)  # OLED 디스플레이 업데이트
        return rms, level
```

### 4. main.py 완전 재설계

```python
# Hardware initialization
initialize_hardware()
├── EMG Sensor (1kHz ADC)
├── Vibration Motor (PWM)
├── RGB LED (3-pin PWM)
└── OLED Display (I2C SSD1306)

# Workflow
Calibration (60초) 
├─ 기준값 설정 (baseline RMS)
└─ LED: 🟢 초록 점등

Monitoring Loop (무한)
├─ 1초마다 EMG 신호 수집
├─ RMS 계산 → 피로도 판정
├─ LED 색상 업데이트 (정상/주의/경고)
├─ OLED에 신호 강도 & 상태 표시
└─ 필요시 진동모터 활성화
```

**main.py 개선사항**:
- config에서 모든 핀 번호 import
- 구조화된 초기화 함수
- 각 단계별 상태 로그 출력 (🟢✓⚠️✕)
- I2C 초기화 실패 시 graceful fallback
- OLED 화면 클리어 등 cleanup

### 5. OLED 디스플레이 표시

기존 OLEDDisplay 클래스 활용:
```
┌─────────────────────────┐
│ BBB  Safety Mode        │  ← 모드 표시
│                         │
│ Fatigue: 75.5%          │  ← 신호 강도 (%)
│ [███████    ]           │  ← 프로그레스 바
│ MF: 0.00 Hz             │  ← Median Frequency (향후)
│ WARNING                 │  ← 상태 텍스트
└─────────────────────────┘
```

### 6. 테스트 업데이트

임계값 변경에 맞게 16개 테스트 모두 업데이트:
- ✅ test_fatigue_normal: >= 90%
- ✅ test_fatigue_warning: 70~90%
- ✅ test_fatigue_critical: < 70%
- ✅ test_alert_on_warning_transition
- ✅ test_alert_on_critical_transition
- ✅ test_no_alert_on_stable_level

**결과**: 16/16 pass ✅

## 사용자 경험 흐름

```
[Init Phase]
1. ESP32-S3 전원 ON (USB-C)
2. 모든 센서/모터 테스트 실행
3. LED 🟢 초록색 점등

[Calibration Phase - 60초]
1. "팔을 완전히 이완하세요" 메시지
2. OLED에 "Fatigue: XX%" 실시간 표시
3. 기준값(baseline RMS) 저장

[Monitoring Phase - 무한 반복]
1. 매초 EMG 샘플링 & RMS 계산
2. LED 색상 변경 (정상→주의→경고)
3. OLED 신호 강도 업데이트
4. 변화 시 진동모터 피드백
   - 정상→주의: 약한 진동 (1회 pulse)
   - 주의→경고: 강한 진동 (연속)

[Shutdown]
Ctrl+C 입력 → LED OFF, OLED 클리어
```

## 기술 구현

### LED 제어 (RGBLEDController)
```python
# 기존 메서드 재사용
led.set_color("normal")    # 🟢 (0, 1023, 0)
led.set_color("warning")   # 🟡 (1023, 512, 0)
led.set_color("critical")  # 🔴 (1023, 0, 0)
```

### OLED 업데이트 (SafetyModeController._update_oled)
```python
display_data = {
    "fatigue_pct": signal_pct,  # (rms / baseline) * 100
    "mf": 0.0,                   # Median Frequency (placeholder)
    "level": level,              # "normal" | "warning" | "critical"
}
self.oled.update(display_data)
```

### 진동모터 강도 (config 기반)
```python
# config.py에서 정의
MOTOR_WARNING_INTENSITY = 800    # 약함
MOTOR_CRITICAL_INTENSITY = 1000  # 강함

# VibratorMotor에서 사용
if level == "warning":
    motor.single_pulse(intensity=MOTOR_WARNING_INTENSITY)
elif level == "critical":
    motor.continuous(intensity=MOTOR_CRITICAL_INTENSITY)
```

## GPIO 최종 핀맵

| 기능 | GPIO | 상태 | 비고 |
|------|------|------|------|
| EMG ADC | GPIO1 | ✅ 확정 | MyoWare 2.0 SIG |
| 진동모터 | GPIO38 | ✅ 사용 중 | PWM 100Hz |
| RGB LED R | GPIO17 | ✅ 사용 중 | PWM 1kHz |
| RGB LED G | GPIO18 | ✅ 사용 중 | PWM 1kHz |
| RGB LED B | GPIO19 | ✅ 사용 중 | PWM 1kHz |
| I2C SDA | GPIO8 | ✅ 확정 | XIAO 기본값 |
| I2C SCL | GPIO9 | ✅ 확정 | XIAO 기본값 |
| 모드 전환 | TBD | 📋 예정 | 택트스위치 |

## 파일 구조

```
firmware/
├── config.py              ← NEW: 중앙화된 설정
├── main.py                ← 완전 재설계: LED + OLED 제어
├── algo/
│   └── emg_processor.py   ← 임계값 조정 (90%, 70%), LED/OLED 메서드 추가
├── sensor/
│   └── emg.py             ← 수정 없음
├── ui/
│   ├── motor.py           ← 수정 없음 (기존 호환)
│   ├── led.py             ← 수정 없음 (기존 호환)
│   └── oled.py            ← 수정 없음 (기존 호환)
└── comm/
    └── wifi.py            ← 수정 없음

tests/
└── test_emg_fatigue.py    ← 임계값에 맞게 업데이트
```

## 배포 체크리스트

- [x] config.py 생성 (핀맵, 임계값, 모터 강도)
- [x] EMGProcessor 임계값 변경 (90%, 70%)
- [x] SafetyModeController LED/OLED 메서드 추가
- [x] main.py 재설계 (LED + OLED 통합)
- [x] 테스트 업데이트 및 전체 통과 (16/16)
- [ ] 실제 하드웨어에서 시뮬레이션 (납땜 후)
- [ ] OLED 표시 검증
- [ ] LED 색상 및 진동모터 강도 최종 확인

## 다음 단계

1. **IMU 센서** (Control Mode 준비)
   - MPU6050 I2C 드라이버 구현
   - Pitch/Roll 각도 계산

2. **실제 하드웨어 통합**
   - MOSFET 회로 납땜
   - 점퍼선 배선
   - 배터리 JST 커넥터 납땜

3. **Control Mode 구현**
   - EMG spike detection (주먹 쥐기)
   - IMU 기반 커서 이동
   - BLE HID Mouse 전송

