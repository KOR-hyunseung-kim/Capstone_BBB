# ESP32-S3 Setup & Testing Guide

## Step 1: Thonny IDE 설치

**Windows에서:**
1. https://thonny.org 접속 → Download 클릭
2. Windows 버전 설치 (.exe)
3. 설치 시 "Install Python package" 체크 (권장)

**또는 pip로:**
```bash
pip install thonny
```

---

## Step 2: MicroPython 펌웨어 플래싱

### 2.1 ESP32-S3을 USB로 연결

- USB-C 케이블로 XIAO ESP32-S3을 노트북에 연결
- 포트 번호 확인 (Windows 장치 관리자에서 COM포트 확인)

### 2.2 Thonny에서 MicroPython 설치

Thonny 실행:
```
메뉴: Tools → Options → Interpreter
```

- **Interpreter** 탭에서 "MicroPython (ESP32)" 선택
- **Port** 에서 USB 포트 선택 (예: COM3, COM5 등)
- **Flash firmware** 버튼 클릭 → 자동으로 최신 버전 설치

**완료 시**:
```
>>> 
```
프롬프트가 보여야 함

---

## Step 3: 펌웨어 코드 업로드

### 3.1 프로젝트 구조

ESP32-S3의 내부 파일 구조:
```
/
├── boot.py              (자동 실행)
├── main.py              (메인 코드)
├── config.py            (설정)
├── sensor/
│   └── emg.py
├── algo/
│   └── emg_processor.py
├── ui/
│   ├── motor.py
│   ├── led.py
│   └── oled.py
└── comm/
    └── wifi.py
```

### 3.2 파일 업로드 (Thonny 사용)

**Thonny 파일 탐색기:**
1. 좌측 "Files" → 우측 "MicroPython device" 
2. 우측 창에서 우클릭 → "New folder" → `sensor`, `algo`, `ui`, `comm` 생성
3. 각 파일을 폴더에 드래그앤드롭

**또는 REPL에서 직접 업로드:**
```
>>> import os
>>> os.listdir('/')
['.fsevent', '.Trashes', 'sys', 'hardware', ...]
```

---

## Step 4: 하드웨어 핀맵 확인

**XIAO ESP32-S3 핀맵:**

| GPIO | 용도 | 연결 |
|------|------|------|
| 1 | EMG ADC | MyoWare 2.0 SIG |
| 8 | I2C SDA | OLED / IMU |
| 9 | I2C SCL | OLED / IMU |
| 17 | LED Red | RGB LED |
| 18 | LED Green | RGB LED |
| 19 | LED Blue | RGB LED |
| 38 | Motor PWM | 진동모터 |

**USB-C 포트:**
- 전원 입력 (5V)
- 시리얼 통신 (Thonny 연결)

---

## Step 5: 테스트 코드 실행

### 5.1 간단한 센서 테스트

Thonny REPL에 입력:
```python
from machine import ADC, Pin

# EMG 센서 테스트
adc = ADC(Pin(1))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

for i in range(10):
    print(f"Sample {i}: {adc.read()}")
    
# 결과 예: 2000~2100 범위의 값이 나와야 함
```

### 5.2 Safety Mode 실행

**main.py 내용:**
```python
# firmware/main.py 를 복사해서 ESP32에 업로드
```

**실행:**
```
Thonny 메뉴 → Run → Run current script
또는 REPL에서: exec(open('main.py').read())
```

**로그 확인:**
```
============================================================
BBB Safety Mode - EMG Fatigue Monitoring with LED + OLED
============================================================
[Init] Initializing hardware...
[Init] EMG sensor... OK
[Init] Vibration motor... OK
[Init] RGB LED... OK
[Init] OLED display... (connected/failed)

[Calib] Entering calibration in 3 seconds...
       WARNING: Please RELAX your arm (no muscle contraction)
       The system will measure your baseline EMG signal

[Calib] Starting 60s calibration...
```

---

## Step 6: 모니터링 로그 확인

Thonny의 Shell 탭에서 실시간 로그:
```
[  10s] OK RMS=2010.5 | Signal= 99.5% | NORMAL
[  20s] OK RMS=2020.3 | Signal=100.1% | NORMAL
[  30s] WARNING RMS=1800.1 | Signal= 89.3% | WARNING
[  40s] CRITICAL RMS=1400.2 | Signal= 69.2% | CRITICAL
[  50s] OK RMS=2050.1 | Signal=101.5% | NORMAL
```

### 로그의 의미:
- `[NNs]` - 경과 시간 (초)
- `OK/WARNING/CRITICAL` - 신호 강도 수준
- `RMS=XXXX` - 현재 RMS 값
- `Signal=%` - 기준값 대비 퍼센트
- `NORMAL/WARNING/CRITICAL` - 피로도 레벨

---

## Step 7: WiFi UDP 통신 (선택)

### 7.1 ESP32 WiFi 설정

**main.py 수정:**
```python
# config.py에서
WIFI_ENABLED = True
WIFI_SSID = "your_wifi_name"
WIFI_PASSWORD = "your_wifi_password"
PC_IP = "192.168.0.100"  # 노트북 IP (ipconfig 에서 확인)
```

### 7.2 PC에서 수신 서버 실행

```bash
python tools/udp_receiver.py
```

### 7.3 데이터 확인

```
[UDP Receiver]
Listening on 0.0.0.0:5005

Received from 192.168.0.50:
EMG data: [2010, 2050, 1990, ...]
```

---

## 트러블슈팅

### 문제: "No module named 'machine'"
```
해결: ESP32가 Thonny에 올바르게 연결되었는지 확인
- USB 케이블 재연결
- 포트 재선택
- Thonny 재시작
```

### 문제: I2C 장치 인식 안 됨
```
해결: 
- OLED/IMU 부품이 정확히 연결되었는지 확인
- main.py에서 try/except로 graceful fallback 처리됨
```

### 문제: ADC 값이 안정적이지 않음
```
해결:
- MyoWare 2.0 센서가 전원을 받는지 확인 (LED 표시 확인)
- 신호 케이블이 제대로 연결되었는지 확인
- 노이즈 제거를 위해 샤이딩 또는 필터 추가
```

### 문제: 프로그램이 자동으로 실행되지 않음
```
해결: boot.py 파일 추가
/boot.py:
import main
```

---

## 다음 단계

1. **정상 작동 확인**
   - [ ] 센서 값이 일정 범위 (1500~2500)에서 움직이는가?
   - [ ] LED가 정상 (초록색)부터 시작하는가?
   - [ ] OLED에 "NORMAL" 상태가 표시되는가?

2. **실제 피로도 테스트**
   - [ ] 팔에 아대를 착용하고 정상 상태 확인
   - [ ] 손가락으로 EMG 센서를 누르면 신호 증가하는가?
   - [ ] 손가락을 계속 누르면 "WARNING" → "CRITICAL"로 변하는가?
   - [ ] LED 색상이 초록 → 주황 → 빨강으로 변하는가?
   - [ ] 진동모터가 작동하는가?

3. **Control Mode 준비**
   - [ ] IMU 센서 추가
   - [ ] 주먹 쥐기 감지 구현
   - [ ] 커서 이동 제어

---

## 참고: 중요한 파일

- **config.py**: GPIO, 임계값, WiFi 설정 (수정 가능)
- **firmware/main.py**: 메인 프로그램 진입점
- **firmware/algo/emg_processor.py**: DSP 알고리즘 (읽기만 권장)
- **firmware/sensor/emg.py**: ADC 드라이버 (읽기만 권장)

