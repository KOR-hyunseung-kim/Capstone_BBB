# BBB Hardware Specification

**작성일**: 2026-05-17  
**상태**: 최종 확정  
**인원**: User  

---

## 1. 부품 구성

| 부품 | 모델 | 수량 | 비고 |
|------|------|------|------|
| MCU | Seeed XIAO ESP32-S3 | 1 | BLE + WiFi + USB-C 충전 |
| EMG 센서 | MyoWare 2.0 | 1 | 근전도 신호 (1kHz ADC) |
| IMU | MPU6050 또는 ICM-20602 | 1 | 6-axis (가속도, 각속도) |
| RGB LED | 5mm RGB | 1 | 상태 표시 (PWM) |
| 진동모터 | Ø10mm 코인형 3V | 1 | 햅틱 피드백 (PWM MOSFET 드라이버) |
| 버튼 스위치 | 4-pin 택트 스위치 | 1 | 모드 전환 (Safety ↔ Control) |
| 배터리 | 3.7V Li-Po 500mAh+ | 1 | USB-C 충전 (내장 회로) |
| MOSFET | 2N7000 | 1 | 모터 드라이버 (3.7V → Motor) |
| 보호 다이오드 | 1N4148 | 1 | 모터 역기전력 보호 |
| 저항 | 100Ω, 220Ω | 2 | 게이트/LED 제한 |

---

## 2. ESP32-S3 GPIO 핀맵

### 2.1 최종 핀 할당

| 기능 | GPIO | 타입 | 설명 |
|------|------|------|------|
| **EMG 신호** | GPIO1 | ADC1_CH0 | MyoWare 2.0 아날로그 신호 입력 |
| **LED Red** | GPIO17 | PWM | RGB LED 적색 채널 |
| **LED Green** | GPIO18 | PWM | RGB LED 녹색 채널 |
| **LED Blue** | GPIO19 | PWM | RGB LED 청색 채널 |
| **진동모터** | GPIO38 | PWM | MOSFET 게이트 드라이브 (3.7V 모터) |
| **I2C SDA** | GPIO8 | I2C | MPU6050/ICM-20602 + OLED (선택) 데이터 |
| **I2C SCL** | GPIO9 | I2C | MPU6050/ICM-20602 + OLED (선택) 클럭 |
| **모드 스위치** | GPIO21 | INPUT_PULLUP | Safety/Control 모드 전환 |
| **3.3V 전원** | 3V3 | Power | 센서, LED, MCU 전원 |
| **배터리 입력** | BAT/5V | Power | Li-Po 3.7V 직결 |
| **그라운드** | GND | Ground | 모든 회로의 공통 접지 |

### 2.2 I2C 버스 구성

**I2C Frequency**: 100 kHz (안정성 우선)

| I2C 주소 | 부품 | 핀 | 비고 |
|----------|------|-----|------|
| 0x68 (104) | MPU6050 IMU | GPIO8(SDA), GPIO9(SCL) | (선택) |
| 0x68/0x69 (104/105) | ICM-20602 IMU | GPIO8(SDA), GPIO9(SCL) | **권장**, SAO=GND면 0x68 |
| 0x3C (60) | OLED SSD1306 | GPIO8(SDA), GPIO9(SCL) | 선택사항 |

**IMU 선택** (`firmware/config.py`):
```python
IMU_TYPE = "ICM20602"  # 또는 "MPU6050"
```

**I2C 주소 확인** (Thonny REPL):
```python
>>> from machine import I2C, Pin
>>> i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
>>> devices = i2c.scan()
>>> print([hex(d) for d in devices])
# [0x68] 또는 [0x69] 출력 (IMU 주소)
```

---

## 3. LED 상태 표시 패턴

### 3.1 색상 코드

**Safety Mode** (EMG 피로도 모니터링):

| 피로도 판정 | LED 색상 | 진동 패턴 | 설명 |
|-----------|---------|---------|------|
| 정상 (< 70% 피로) | **녹색** | 조용 | 신호 강도 >= 90% baseline |
| 주의 (70~90% 피로) | **황색** | 짧은 진동, 긴 텀 | 신호 강도 70~90% baseline |
| 경고 (>= 90% 피로) | **적색** | 짧은 진동, 짧은 텀 | 신호 강도 < 70% baseline |

**Control Mode** (IMU 커서 제어):

| 상태 | LED 색상 | 진동 | 설명 |
|------|---------|------|------|
| 대기 | **녹색** | 조용 | 커서 이동 준비 상태 |
| 클릭 감지 | **황색** | 짧은 진동 1회 | EMG 스파이크 감지 → BLE HID 클릭 송신 |
| 오류 | **적색** | 강진동 | 센서 연결 실패 또는 과부하 |

### 3.2 RGB PWM 값 (0~1023)

```python
# 색상 정의 (PWM Duty Cycle)
colors = {
    "green": (0, 1023, 0),      # 정상: 녹색
    "yellow": (1023, 512, 0),   # 주의: 황색
    "red": (1023, 0, 0),        # 경고: 적색
    "off": (0, 0, 0),           # 꺼짐
}
```

---

## 4. 진동모터 피드백 패턴

### 4.1 진동 패턴 정의

**Safety Mode (EMG 피로도)**:

| 상태 | 패턴 | 설명 |
|------|------|------|
| 평시 | 조용 | 진동 없음 (PWM 0%) |
| 주의 | 짧은 진동 + 긴 텀 | ON: 100ms, OFF: 500ms (반복 2회) |
| 경고 | 짧은 진동 + 짧은 텀 | ON: 100ms, OFF: 200ms (반복 3회) |

**Control Mode (IMU 클릭)**:

| 상태 | 패턴 | 설명 |
|------|------|------|
| 클릭 감지 | 싱글 펄스 | ON: 100ms, 강도: 800/1023 (약 중간) |

### 4.2 PWM 강도 설정

```python
# 진동 강도 (PWM Duty Cycle, 0~1023)
MOTOR_OFF = 0           # 진동 없음
MOTOR_LOW = 600         # 약한 진동
MOTOR_MEDIUM = 800      # 중간 진동
MOTOR_HIGH = 1000       # 강한 진동 (최대)

# 패턴 타이밍 (ms)
PULSE_SHORT = 100       # 짧은 진동
INTERVAL_LONG = 500     # 긴 간격 (주의)
INTERVAL_SHORT = 200    # 짧은 간격 (경고)
```

---

## 5. 모드 전환 (버튼 스위치)

### 5.1 버튼 동작

| 누름 시간 | 동작 | 결과 |
|----------|------|------|
| 짧게 (< 1초) | 모드 전환 | Safety ↔ Control |
| 길게 (> 2초) | 펌웨어 리셋 | ESP32-S3 재부팅 |

### 5.2 GPIO 설정

```python
from machine import Pin

mode_switch = Pin(21, Pin.IN, Pin.PULL_UP)
# 누르면 0, 놓으면 1
if mode_switch.value() == 0:
    print("버튼 눌림")
```

---

## 6. 전원 분배

### 6.1 전압 레벨

| 부품 | 공급 전압 | 경로 |
|------|----------|------|
| ESP32-S3 MCU | 3.3V | Li-Po → 내장 LDO |
| MyoWare 2.0 | 3.3V | LDO 출력 |
| MPU6050 IMU | 3.3V | LDO 출력 |
| RGB LED | 3.3V | GPIO PWM (LDO) |
| 진동모터 | 3.7V | 배터리 직결 (MOSFET 드라이버) |

### 6.2 전류 예산

| 부품 | 최대 전류 | 비고 |
|------|----------|------|
| ESP32-S3 | 80 mA | WiFi/BLE 포함 |
| MyoWare 2.0 | 10 mA | 신호처리 |
| MPU6050 | 3.7 mA | I2C 통신 |
| RGB LED (full) | 60 mA | 세 채널 모두 ON |
| 진동모터 | 200 mA @ 3.7V | 피크 전류 |
| **총계** | **300+ mA** | **배터리 2시간 이상 보장** |

---

## 7. I2C 회로 설계

### 7.1 풀업 저항

```
         +3.3V
           |
         [4.7kΩ]  ← 풀업 저항 (모듈 내장 보통)
           |
    GPIO8 ─┤
    (SDA)  └─→ MPU6050 SDA, OLED SDA (병렬)

         +3.3V
           |
         [4.7kΩ]  ← 풀업 저항 (모듈 내장 보통)
           |
    GPIO9 ─┤
    (SCL)  └─→ MPU6050 SCL, OLED SCL (병렬)
```

### 7.2 MicroPython 초기화

```python
from machine import I2C, Pin

# I2C 버스 생성
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100_000)

# 연결된 장치 확인
devices = i2c.scan()
print(f"I2C devices: {devices}")  # [104, 60] 또는 [0x68, 0x3C]
```

---

## 8. EMG 신호 처리 설정

### 8.1 ADC 구성

```python
from machine import ADC, Pin

emg = ADC(Pin(1))  # GPIO1 = ADC1_CH0
emg.atten(ADC.ATTN_11DB)   # 0~3.3V 범위
emg.width(ADC.WIDTH_12BIT)  # 12-bit 해상도
```

### 8.2 신호 범위

| 상태 | ADC 범위 | mV 범위 | 신호 강도 |
|------|---------|---------|----------|
| 휴식 (정상 신호) | 500~1500 | 400~1200 | 100% |
| 약한 수축 | 1500~2500 | 1200~2000 | 70~90% |
| 강한 수축 | 2500~4095 | 2000~3300 | < 70% (피로) |

### 8.3 피로도 판정 로직

```python
# 신호 강도 = (baseline - current_rms) / baseline * 100
# threshold 기준:
# - EMG_NORMAL_THRESHOLD = 90%   → 신호 강도 >= 90% → 정상 (녹색)
# - EMG_WARNING_THRESHOLD = 70%  → 신호 강도 70~90% → 주의 (황색)
# - < 70%                        → 신호 강도 < 70% → 경고 (적색)
```

---

## 9. 핀 배치도 (다이어그램)

```
         ┌─────────────────────────────────┐
         │   Seeed XIAO ESP32-S3          │
         │                                 │
    좌측 │  GND                        GND │우측
         │  IO43    IO9 (SCL)              │
         │  IO45    IO8 (SDA)              │
         │  IO46    IO7                    │
         │  IO3     IO6                    │
         │  IO2     IO5                    │
         │  IO1(EMG) IO4                   │
         │  IO42    IO38 (Motor)           │
         │  IO41    IO37                   │
         │  IO40    IO36                   │
         │  IO39    IO35                   │
         │  IO38    IO0                    │
         │  3V3     5V (BAT)               │
         │  GND     GND                    │
         │                                 │
         │  GPIO17 (LED_R)                 │
         │  GPIO18 (LED_G)                 │
         │  GPIO19 (LED_B)                 │
         │  GPIO21 (Mode Switch)           │
         │                                 │
         └─────────────────────────────────┘
```

---

## 10. 관련 소스 코드

| 파일 | 설명 |
|------|------|
| `firmware/config.py` | 모든 GPIO 핀 정의, IMU 타입 선택, 임계값 설정 |
| `firmware/sensor/emg.py` | EMG 센서 드라이버 |
| `firmware/sensor/imu.py` | IMU (MPU6050) 드라이버 |
| `firmware/sensor/icm20602.py` | IMU (ICM-20602) 드라이버 **← 권장** |
| `firmware/ui/led.py` | RGB LED 컨트롤러 |
| `firmware/ui/motor.py` | 진동모터 컨트롤러 |
| `firmware/safety_mode.py` | Safety Mode 구현 |
| `firmware/control_mode.py` | Control Mode 구현 (IMU 타입 자동 선택) |

---

## 11. 검증 체크리스트

**전원 연결 전**:
- [ ] 모든 핀 극성 확인 (특히 배터리)
- [ ] 저항값 확인 (100Ω, 220Ω)
- [ ] MOSFET 방향 확인 (TO-92)
- [ ] 다이오드 방향 확인 (띠 = 캐소드)

**배터리 연결 후**:
- [ ] ESP32-S3 부팅 확인 (LED 점멸)
- [ ] GPIO1 (EMG) 신호 확인 (500~1500 ADC)
- [ ] I2C 버스 스캔 (0x68, 0x3C 감지)
- [ ] GPIO38 모터 테스트 (진동 감지)
- [ ] GPIO17/18/19 LED 색상 확인

**소프트웨어 테스트**:
- [ ] Safety Mode: 피로도 판정 로직 검증
- [ ] Control Mode: IMU 기반 커서 이동 테스트
- [ ] 모드 전환: GPIO21 버튼 반응 확인
- [ ] WiFi 통신: UDP 데이터 수신 (선택)

---

## 12. 상태 변경 이력

| 날짜 | 항목 | 변경 내용 |
|------|------|---------|
| 2026-05-17 | ICM-20602 추가 | IMU 센서 선택 기능 추가 (MPU6050 또는 ICM-20602) |
| 2026-05-17 | HW 스펙 확정 | RGB LED + 진동모터 패턴 정의, 핀맵 최종 확정 |
| 2026-05-05 | 초기 핀맵 | GPIO20 진동모터 (추후 GPIO38로 변경) |

---
