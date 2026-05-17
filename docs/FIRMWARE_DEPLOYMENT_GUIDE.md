# BBB 펌웨어 배포 & 테스트 가이드

**작성일**: 2026-05-17  
**대상**: ESP32-S3 XIAO 보드 + 센서 하드웨어  

---

## 1단계: 하드웨어 준비

### 1.1 물리적 구성

**참고 문서**: `docs/02_HW/HW_SPEC.md` → 섹션 4 (납땜 순서)

**체크리스트**:
- [ ] ESP32-S3 XIAO 보드 준비 (기존 헤더 확인)
- [ ] MOSFET 회로 조립 (만능기판 또는 브레드보드)
  - 2N7000 MOSFET, 1N4148 다이오드, 100Ω 저항
- [ ] EMG 센서 연결 (GPIO1 ADC)
- [ ] IMU 센서 연결 (GPIO8/9 I2C)
- [ ] RGB LED 연결 (GPIO17/18/19 PWM)
- [ ] 진동모터 연결 (GPIO38 PWM + MOSFET)
- [ ] 모드 스위치 연결 (GPIO21 INPUT_PULLUP)
- [ ] 배터리 JST 커넥터 연결 (맨 마지막!)

### 1.2 배선 검증

**도통 테스트** (배터리 연결 전):
```bash
멀티미터 사용:
- 배터리 (+) ─ LED (-): 3.7V
- 배터리 (-) ─ LED (+): 0V (단절, 정상)
```

**극성 확인** ⚠️:
- 배터리 극성 (+ 빨강, - 검정)
- LED 극성 (공통 캐소드/애노드)
- MOSFET 방향 (TO-92: 1=G, 2=S, 3=D)

---

## 2단계: 펌웨어 준비

### 2.1 필요한 파일

**ESP32에 복사해야 할 파일 구조**:

```
esp32-storage/
├── main.py                    ← 메인 진입점 (부팅 시 자동 실행)
├── boot.py                    ← 부팅 스크립트 (선택)
├── config.py                  ← 중앙 설정 파일 (필수)
│
├── sensor/
│   ├── emg.py                ← EMG 드라이버
│   ├── imu.py                ← MPU6050 드라이버
│   └── icm20602.py           ← ICM-20602 드라이버 (선택)
│
├── ui/
│   ├── led.py                ← RGB LED 제어
│   ├── motor.py              ← 진동모터 제어
│   └── oled.py               ← OLED 디스플레이 (선택)
│
├── comm/
│   └── wifi.py               ← WiFi 통신 (선택, 추후)
│
├── safety_mode.py            ← Safety Mode 구현
├── control_mode.py           ← Control Mode 구현
│
└── algo/                      ← (기존 파일, 필요 시)
    ├── emg_processor.py
    ├── control.py
    └── kalman_filter.py
```

**최소 필수 파일** (기본 테스트):
```
main.py
config.py
safety_mode.py
control_mode.py
sensor/emg.py
sensor/imu.py (또는 icm20602.py)
ui/led.py
ui/motor.py
```

### 2.2 MicroPython 버전 확인

```bash
# Thonny IDE 또는 터미널에서 확인
>>> import sys
>>> print(sys.version)

# 권장 버전: MicroPython 1.20+ (ESP32-S3 port)
```

**필요 시 펌웨어 업데이트**:
```bash
# esptool.py 사용
esptool.py --chip esp32-s3 -p /dev/ttyUSB0 erase_flash
esptool.py --chip esp32-s3 -p /dev/ttyUSB0 write_flash -z 0x0 esp32-s3-20240105-v1.22.2.bin
```

---

## 3단계: 펌웨어 배포

### 3.1 Thonny IDE를 이용한 배포 (권장)

**설치 & 설정**:
1. [Thonny 다운로드](https://thonny.org) → 설치
2. **Tools** → **Options** → **Interpreter**
   - 선택: `MicroPython (ESP32)`
   - Port: `/dev/ttyUSB0` (또는 `COM3` on Windows)
   - Baud rate: `115200`

**파일 전송**:
1. Thonny 좌측 "Files" 패널에서 `/` (루트) 선택
2. 우측 마우스 클릭 → **Upload to /** (또는 드래그 앤 드롭)
3. 폴더별 업로드 순서:
   - `config.py` (먼저)
   - `sensor/` 폴더 → 모든 파일
   - `ui/` 폴더 → 모든 파일
   - `comm/` 폴더 (선택)
   - `safety_mode.py`, `control_mode.py`
   - `main.py` (마지막)

**확인**:
```python
# Thonny REPL에서 실행
>>> import os
>>> os.listdir()
['config.py', 'main.py', 'safety_mode.py', 'control_mode.py', 'sensor', 'ui', ...]
```

### 3.2 명령줄을 이용한 배포

```bash
# ampy 도구 사용 (Python 패키지)
pip install adafruit-ampy

# 파일 업로드
ampy -p /dev/ttyUSB0 put config.py
ampy -p /dev/ttyUSB0 put main.py
ampy -p /dev/ttyUSB0 put safety_mode.py
ampy -p /dev/ttyUSB0 put control_mode.py

# 폴더 업로드
ampy -p /dev/ttyUSB0 put sensor
ampy -p /dev/ttyUSB0 put ui
```

---

## 4단계: 테스트 시작

### 4.1 부팅 테스트

**연결 방법**:
1. ESP32를 USB-C 케이블로 PC에 연결
2. Thonny IDE REPL에서 확인 (자동 연결)

**부팅 확인**:
```
=======================================================================
BBB (Bio Body Band) - Dual Mode Firmware
=======================================================================
[INFO] Available Modes:
  1. Safety Mode   - EMG fatigue monitoring (LED + Motor feedback)
  2. Control Mode  - Arm tilt cursor control + EMG click detection
[INFO] Mode Switch: GPIO21 Button (tap to switch, hold to reset)
=======================================================================

[CONFIG] Hardware Configuration:
  EMG Sensor:     ENABLED
  IMU Sensor:     ENABLED
  RGB LED:        ENABLED
  Vibrator Motor: ENABLED
  OLED Display:   DISABLED

[CONFIG] Debug Settings:
  Global DEBUG:     ON
  Safety Mode:      VERBOSE
  Control Mode:     VERBOSE
```

✅ 위 메시지가 출력되면 부팅 성공!

### 4.2 단계별 테스트

#### A. Safety Mode 테스트

**시작**:
```
=======================================================================
SAFETY MODE - EMG Fatigue Monitoring
=======================================================================
[Setup] Calibration: Keep arm RELAXED, no muscle contraction
[SafetyMode] Calibration starting (60s)...
[SafetyMode] EMG sensor initialized
[SafetyMode] LED controller initialized
[SafetyMode] Motor controller initialized
```

**체크리스트**:
- [ ] LED가 녹색으로 점등 (calibration 중)
- [ ] 60초 동안 "10s... 20s... 30s..." 출력
- [ ] Baseline RMS 값 출력: `[SafetyMode] Calibration complete. Baseline RMS: XXXX`

**실제 동작 테스트**:
```
1단계: 팔을 이완 상태 유지
  → LED: 녹색 (🟢 Normal)
  → 진동: 없음
  → 출력: "Level: normal"

2단계: 가볍게 근육 수축 (약 10초)
  → LED: 황색 (🟡 Warning)
  → 진동: 100ms ON, 500ms OFF 반복
  → 출력: "Fatigue: XX.X%, Level: warning"

3단계: 강하게 근육 수축 (약 10초)
  → LED: 적색 (🔴 Critical)
  → 진동: 100ms ON, 200ms OFF 반복
  → 출력: "Fatigue: XX.X%, Level: critical"
```

#### B. Control Mode 테스트

**시작** (GPIO21 버튼 누르면 전환):
```
=======================================================================
CONTROL MODE - IMU Cursor Control + EMG Click
=======================================================================
[Setup] IMU Sensor: ICM20602
[Setup] IMU Calibration: Keep arm still, level
[ControlMode] IMU sensor (ICM20602) initialized
[ControlMode] Calibration starting (5s)...
```

**체크리스트**:
- [ ] LED가 녹색으로 점등
- [ ] 5초 동안 캘리브레이션 수행
- [ ] IMU 각도 값 출력

**실제 동작 테스트**:
```
1단계: 팔을 중립 위치 유지
  → LED: 녹색 (🟢 Ready)
  → 커서: 중앙 (512, 512)

2단계: 팔을 앞으로 기울임 (pitch)
  → 커서 Y값 감소 (↑ 위로)
  → 출력: "Pitch: 30.0°, Cursor: (512, 200)"

3단계: 팔을 옆으로 기울임 (roll)
  → 커서 X값 변화 (← 또는 →)
  → 출력: "Roll: -20.0°, Cursor: (200, 512)"

4단계: 주먹을 쥐기 (EMG spike)
  → LED: 황색 (🟡 Click detected)
  → 진동: 100ms 싱글 펄스
  → 출력: "EMG: 3500+, Click: True"
```

---

## 5단계: 문제 해결

### 5.1 일반적인 오류

#### "ModuleNotFoundError: No module named 'config'"
```
해결: config.py가 ESP32 루트에 있는지 확인
Thonny Files 패널: os.listdir() 에서 'config.py' 확인
```

#### "I2C device not found (0x68 / 0x69)"
```
확인 사항:
1. GPIO8(SDA), GPIO9(SCL) 배선 확인
2. I2C 풀업 저항 (모듈에 내장 확인)
3. 센서 전원 3.3V 확인
4. I2C 주소 확인:
   >>> from machine import I2C, Pin
   >>> i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
   >>> print(i2c.scan())  # [104] (0x68) 또는 [105] (0x69) 출력되어야 함
```

#### "ADC read always returns 0 or 4095"
```
확인 사항:
1. EMG 센서 전원 3.3V 확인
2. GPIO1 배선 확인
3. 신호 선 스크린핑 추가 (간섭 제거)
4. 테스트:
   >>> from sensor.emg import EMGSensor
   >>> emg = EMGSensor(1)
   >>> print(emg.read_raw())  # 500~3000 범위여야 함
```

#### "진동모터가 작동하지 않음"
```
확인 사항:
1. GPIO38 + MOSFET 배선 확인
2. 배터리 극성 확인 (배터리 (+) → 모터 (+))
3. 2N7000 핀 배치 확인:
   - Gate: GPIO38 (100Ω 거쳐서)
   - Source: GND
   - Drain: 모터 (-)
4. 1N4148 다이오드 극성 확인
5. 테스트:
   >>> from machine import PWM, Pin
   >>> motor = PWM(Pin(38))
   >>> motor.freq(100)
   >>> motor.duty(800)  # 진동 시작
   >>> motor.duty(0)    # 진동 중지
```

### 5.2 성능 문제

#### 반응 속도가 느림
```
원인: Calibration 시간 너무 김 (config.py)
해결: 
  CALIBRATION_DURATION_SEC = 30  # 60에서 30으로 줄임
  (또는 테스트 시에만 5초로 단축)
```

#### Debug 메시지가 너무 많음
```
해결 (config.py):
  DEBUG = False
  DEBUG_SAFETY_MODE = False
  DEBUG_CONTROL_MODE = False
  (또는 특정 항목만 True)
```

---

## 6단계: 최적화 & 배포

### 6.1 Config 튜닝

**Safety Mode**:
```python
EMG_NORMAL_THRESHOLD = 90      # 정상/주의 경계 (%)
EMG_WARNING_THRESHOLD = 70     # 주의/경고 경계 (%)
CALIBRATION_DURATION_SEC = 30  # 캘리브레이션 시간 (초)
```

**Control Mode**:
```python
CURSOR_SPEED_FACTOR = 15       # 커서 민감도 (낮을수록 느림)
EMG_SPIKE_THRESHOLD = 3200     # 클릭 감지 임계값 (낮을수록 민감)
COMPLEMENTARY_FILTER_ALPHA = 0.97  # IMU 안정성 (높을수록 부드러움)
```

### 6.2 배터리 수명 테스트

```python
# 비활성 상태 (모드 선택 대기)
- 예상 전류: < 50mA
- 2시간 배터리: 약 100mAh 소비

# Safety Mode 활성 (EMG 샘플링)
- 예상 전류: 100~150mA
- 배터리: 2시간 이상 보장

# Control Mode 활성 (IMU 100Hz + EMG)
- 예상 전류: 150~200mA
- 배터리: 1.5~2시간
```

**측정 방법**:
```python
# Thonny에서 시간 측정
import time
start = time.ticks_ms()
# ... 실행 ...
elapsed = time.ticks_diff(time.ticks_ms(), start)
print(f"경과 시간: {elapsed}ms ({elapsed/1000}초)")
```

### 6.3 배포용 최종 config

```python
# production-ready config.py
DEBUG = False
DEBUG_SAFETY_MODE = False
DEBUG_CONTROL_MODE = False
DEBUG_EMG_VALUES = False
DEBUG_IMU_VALUES = False
DEBUG_LED_CONTROL = False
DEBUG_MOTOR_CONTROL = False
DEBUG_CALIBRATION = False

ENABLE_EMG_SENSOR = True
ENABLE_IMU_SENSOR = True
ENABLE_MOTOR = True
ENABLE_LED = True
ENABLE_OLED = False  # WiFi 전송 대신 OLED 비활성화

# 최적화된 임계값
CALIBRATION_DURATION_SEC = 30  # 빠른 시작
EMG_NORMAL_THRESHOLD = 90
EMG_WARNING_THRESHOLD = 70
```

---

## 7단계: WiFi 통신 (추후)

현재는 로컬 테스트만 진행합니다.
WiFi 통신 구현은 별도 스펙 문서 참고.

---

## 체크리스트 (전체)

### 하드웨어
- [ ] ESP32-S3 XIAO 준비
- [ ] 회로 납땜 완료 (HW_SPEC 참고)
- [ ] 배선 도통 테스트 통과
- [ ] 배터리 극성 확인

### 펌웨어
- [ ] 펌웨어 파일 모두 ESP에 업로드
- [ ] config.py 설정 확인
- [ ] main.py 부팅 확인

### Safety Mode
- [ ] Calibration 60초 완료
- [ ] LED 색상 변화 확인 (녹→황→적)
- [ ] 모터 진동 패턴 확인 (조용→긴텀→짧은텀)

### Control Mode
- [ ] IMU 캘리브레이션 완료
- [ ] 팔 기울기에 따른 커서 이동 확인
- [ ] 주먹 쥐기로 클릭 감지 확인
- [ ] 모드 전환 버튼 작동 확인

### 최적화
- [ ] Config 임계값 튜닝
- [ ] 배터리 수명 확인 (2시간 목표)
- [ ] Debug 메시지 비활성화 (배포용)

---

## 다음 단계

**2단계 (WiFi 통신)**:
- `comm/wifi.py` 완성
- PC 수신 서버 연동
- 데이터 시각화

**3단계 (BLE HID)**:
- BLE HID 마우스 구현
- Windows/Mac/Linux 호환성 테스트

**4단계 (하우징 & 최종 테스트)**:
- 3D 프린팅 하우징
- 사용자 피드백 반영
- 배터리 지속시간 최적화

---
