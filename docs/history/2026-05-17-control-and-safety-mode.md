# Control Mode & Safety Mode Implementation

**날짜**: 2026-05-17  
**작업자**: Claude AI  
**상태**: 완료  

---

## 요약

HW 스펙 확정 후, **Safety Mode**와 **Control Mode** 두 가지 동작 모드를 MicroPython으로 완전 구현했습니다.
- **Safety Mode**: EMG 피로도 모니터링 → RGB LED + 진동모터 패턴
- **Control Mode**: IMU 팔 기울기 + EMG 클릭 → 커서 제어

---

## 결정 사항

### 1. HW 스펙 최종 확정

**파일**: `docs/02_HW/HW_SPEC.md` (신규 생성)

**핀맵** (ESP32-S3 XIAO):
| 기능 | GPIO | 타입 |
|------|------|------|
| EMG 신호 | GPIO1 | ADC1_CH0 |
| LED Red | GPIO17 | PWM |
| LED Green | GPIO18 | PWM |
| LED Blue | GPIO19 | PWM |
| 진동모터 | GPIO38 | PWM (MOSFET) |
| I2C SDA | GPIO8 | I2C |
| I2C SCL | GPIO9 | I2C |
| 모드 스위치 | GPIO21 | INPUT_PULLUP |

### 2. LED 색상 패턴 (Safety Mode)

```
신호 강도    |  LED 색상  |  설명
≥ 90%      |  🟢 Green   |  정상 (피로 < 70%)
70~90%     |  🟡 Yellow  |  주의 (피로 70~90%)
< 70%      |  🔴 Red     |  경고 (피로 > 90%)
```

### 3. 진동모터 패턴 (Safety Mode)

```
상태       |  패턴                    |  강도
정상       |  조용 (OFF)              |  0%
주의       |  100ms ON, 500ms OFF     |  800/1023
경고       |  100ms ON, 200ms OFF     |  1000/1023
```

### 4. Control Mode 피드백

- **커서 이동**: IMU 가속도 → Complementary Filter → Pitch/Roll → 커서 좌표
- **클릭**: EMG 스파이크 (ADC > 3500) 감지 → 싱글 펄스 진동
- **LED**: 대기 (녹색) → 클릭 감지 (황색) → 오류 (적색)

---

## 변경된 파일

### 신규 파일

1. **`firmware/safety_mode.py`** (280줄)
   - `SafetyMode` 클래스: EMG 피로도 모니터링
   - Baseline 캘리브레이션 (60초)
   - 실시간 피로도 판정 + LED/모터 제어
   - 모드 전환 버튼 감지

2. **`firmware/control_mode.py`** (320줄)
   - `ComplementaryFilter` 클래스: IMU 각도 융합
   - `ControlMode` 클래스: 커서 제어 + EMG 클릭 감지
   - IMU 캘리브레이션 (가속도 & 자이로)
   - Pitch/Roll 계산 → 커서 좌표 변환

3. **`docs/02_HW/HW_SPEC.md`** (400줄)
   - 부품 구성표 (11개 부품)
   - GPIO 최종 핀맵
   - I2C 버스 구성 (MPU6050 0x68, OLED 0x3C 선택)
   - LED/모터 패턴 상세 정의
   - 전원 분배 및 전류 예산
   - 검증 체크리스트

### 수정 파일

1. **`firmware/main.py`** (완전 재작성)
   - 기존: Safety Mode 전용
   - 변경: 듀얼 모드 매니저 (Safety ↔ Control 전환)
   - 부팅 시 모드 선택 (기본값: Safety Mode)
   - 모드별 시작 배너 및 안내

---

## 핵심 로직

### Safety Mode 동작 흐름

```python
1. 초기화 (EMG, LED, 모터)
2. Baseline 캘리브레이션 (60초 휴식 신호 수집)
3. 실시간 모니터링 루프:
   - EMG 샘플링 (1kHz, 1000 샘플 = 1초)
   - RMS 계산
   - 신호 강도 (baseline 대비 %) 계산
   - 피로도 판정 (Normal/Warning/Critical)
   - LED 색상 업데이트
   - 진동 패턴 실행 (긴 텀 또는 짧은 텀)
   - GPIO21 버튼 감지 → Control Mode로 전환
4. 종료 시 모터 STOP, LED OFF
```

### Control Mode 동작 흐름

```python
1. 초기화 (IMU, EMG, LED, 모터)
2. IMU 캘리브레이션 (5초, 가속도 & 자이로)
3. 실시간 커서 제어 루프:
   - IMU 데이터 읽기 (가속도 3축, 자이로 3축)
   - Complementary Filter로 Pitch/Roll 계산
   - 팔 기울기 → 커서 좌표 변환
   - EMG 스파이크 감지 (ADC > 3500)
   - 스파이크 시 진동 + LED 황색 점멸
   - GPIO21 버튼 감지 → Safety Mode로 전환
4. 종료 시 모터 STOP, LED OFF
```

### Complementary Filter (IMU Fusion)

```python
alpha = 0.98  # 자이로 가중치 (99%)
dt = 0.01     # 시간 간격 (10ms)

pitch = alpha * (prev_pitch + gy * dt) + (1 - alpha) * accel_pitch
roll  = alpha * (prev_roll + gx * dt) + (1 - alpha) * accel_roll
```

**특징**:
- 자이로: 단기 변화에 민감 (떨림 감지)
- 가속도: 장기 드리프트 보정 (누적 오차 제거)
- 결합: 부드러우면서 빠른 응답

---

## 테스트 계획

### Safety Mode 검증

```
1. Calibration 단계
   - [ ] 60초 동안 EMG 신호 수집
   - [ ] Baseline RMS 계산 및 출력

2. Monitoring 단계
   - [ ] 정상 상태: LED 녹색, 진동 없음
   - [ ] 약간 피곤: LED 황색, 100ms 진동 + 500ms 간격
   - [ ] 많이 피곤: LED 적색, 100ms 진동 + 200ms 간격

3. 모드 전환
   - [ ] GPIO21 버튼 누르면 Control Mode로 전환
```

### Control Mode 검증

```
1. Calibration 단계
   - [ ] IMU 가속도 캘리브레이션
   - [ ] IMU 자이로 캘리브레이션

2. Cursor Control
   - [ ] 팔을 앞으로 기울임 → 커서 위로 이동
   - [ ] 팔을 뒤로 기울임 → 커서 아래로 이동
   - [ ] 팔을 좌측으로 기울임 → 커서 좌측 이동
   - [ ] 팔을 우측으로 기울임 → 커서 우측 이동

3. Click Detection
   - [ ] 주먹을 쥐면 EMG 스파이크 감지
   - [ ] LED 황색으로 변경
   - [ ] 진동 1회 발생

4. 모드 전환
   - [ ] GPIO21 버튼 누르면 Safety Mode로 전환
```

---

## 다음 단계

### 즉시 (2~3일)

1. **ESP32-S3에서 실행 테스트**
   - 두 모드 모두 부팅 후 동작 확인
   - 모드 전환 버튼 반응 테스트
   - LED/모터 피드백 확인

2. **Calibration 검증**
   - Safety Mode: EMG 베이스라인 정확성
   - Control Mode: IMU 각도 정확성 (±5° 오차 목표)

3. **임계값 튜닝**
   - EMG 스파이크 임계값 (현재 3500): 사용자 맞춤
   - 커서 이동 속도: 팔 기울기 정도에 따라 조정

### 2주 내

4. **WiFi 통신 연동** (Safety Mode)
   - ESP32 → PC UDP 전송
   - 피로도 데이터 실시간 모니터링

5. **BLE HID 마우스** (Control Mode)
   - 커서 좌표 → BLE 패킷 변환
   - 클릭 신호 → BLE HID Button 송신
   - Windows/Mac/Linux 호환성 테스트

6. **사용자 피드백**
   - 편의성 개선 (버튼 반응도, LED 밝기, 진동 강도)
   - 배터리 수명 측정 (2시간 목표)

---

## 기술 노트

### EMG 피로도 판정 (Signal Drop)

```
Baseline RMS: 1000 (60초 휴식 중 측정)
Current RMS:  800  (실시간 측정)

Signal Strength = (Current RMS / Baseline RMS) * 100
                = (800 / 1000) * 100 = 80%

Fatigue Judgment:
- ≥ 90% → Normal (정상, 피로 없음)
- 70~90% → Warning (주의, 약간 피곤)
- < 70% → Critical (경고, 많이 피곤)
```

### 자이로 드리프트 보정

**문제**: 자이로만 사용하면 각도가 점점 늘어남 (1°/분 정도)

**해결**: Complementary Filter로 가속도 측정값으로 보정
- 자이로: 빠른 변화 감지 (응답성 좋음)
- 가속도: 장기 드리프트 제거 (정확성 좋음)
- 결합: 둘의 장점 취함

### 계수 (Alpha) 선택

```python
alpha = 0.98  # 자이로 98%, 가속도 2%
- 자이로 의존도 높음 → 빠른 응답, 떨림 감지
- alpha = 0.95 (자이로 95%, 가속도 5%): 더 부드러움
- alpha = 0.99 (자이로 99%, 가속도 1%): 더 빠름
```

---

## 파일 구조

```
firmware/
├── main.py              ← [수정] 듀얼 모드 매니저
├── safety_mode.py       ← [신규] Safety Mode 구현
├── control_mode.py      ← [신규] Control Mode 구현
├── config.py            ← [기존] 핀맵 정의
├── sensor/
│   ├── emg.py          ← [기존] EMG 드라이버
│   └── imu.py          ← [기존] IMU (MPU6050) 드라이버
├── ui/
│   ├── led.py          ← [기존] RGB LED 제어
│   └── motor.py        ← [기존] 진동모터 제어
└── comm/
    └── wifi.py         ← [기존] WiFi UDP 통신 (추후)

docs/
└── 02_HW/
    └── HW_SPEC.md      ← [신규] HW 스펙 (최종)
```

---

## 커밋 메시지

```
feat: implement Safety Mode and Control Mode with mode switching

Safety Mode:
- EMG-based fatigue monitoring with 60s baseline calibration
- Real-time signal strength calculation (baseline comparison)
- Fatigue level judgment: Normal (<70%) → Warning (70-90%) → Critical (>90%)
- LED feedback: Green → Yellow → Red
- Motor haptic patterns: Silent → Long interval pulses → Short interval pulses

Control Mode:
- IMU-based arm tilt cursor control (pitch/roll to X/Y movement)
- Complementary filter for angle fusion (accel + gyro)
- EMG spike detection for mouse click (ADC > 3500)
- Motor pulse on click detection

Main Firmware:
- Dual-mode operation with GPIO21 button switching
- Mode-specific startup banners and calibration
- Error handling and graceful shutdown

Hardware Specification:
- Final pinmap for ESP32-S3 XIAO (11 components)
- I2C bus configuration (MPU6050, optional OLED)
- Power distribution and current budgeting
- Detailed verification checklist

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## 참고 자료

- `docs/flow.md` — 전체 진행 상황 (갱신 예정)
- `docs/02_HW/HW_SPEC.md` — HW 최종 스펙
- `firmware/config.py` — 모든 GPIO/임계값 설정
- CLAUDE.md — 프로젝트 전체 개발 프로세스

---
