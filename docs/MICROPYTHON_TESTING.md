# MicroPython Kalman Filter Testing (ESP32-S3)

ESP32-S3 보드에서 칼만 필터를 MicroPython으로 직접 테스트하는 가이드입니다.

## 빠른 시작

### 1. PC에서 먼저 테스트

```bash
# PC의 Python 3.11+에서 실행 (모든 test 통과 확인)
python firmware/test_kalman_micropython.py
```

결과:
```
============================================================
RESULTS: 14/14 tests passed
============================================================
[SUCCESS] Kalman Filter ready for deployment
```

### 2. ESP32-S3에 파일 전송

#### 방법 A: Thonny IDE 사용 (권장)

1. **Thonny 다운로드**: https://thonny.org/
2. **ESP32-S3 연결**
   - USB-C 케이블로 PC와 연결
   - Thonny → Tools → Options → Interpreter → MicroPython (ESP32)
   - Port: COM (자동 감지)
3. **파일 업로드**
   - `firmware/test_kalman_micropython.py`를 보드에 복사
   - 우클릭 → Upload to /

#### 방법 B: ampy 명령줄 도구

```bash
# 설치
pip install adafruit-ampy

# ESP32-S3의 시리얼 포트 확인
python -m serial.tools.list_ports

# 파일 업로드
ampy --port COM5 put firmware/test_kalman_micropython.py test_kalman.py

# 테스트 실행
ampy --port COM5 run test_kalman.py
```

#### 방법 C: esptool을 이용한 업로드

```bash
# MicroPython 바이너리 플래싱 (처음 한 번만)
esptool.py --chip esp32-s3 --port COM5 write_flash -z 0x0 esp32-s3_firmware.bin

# 파일 업로드 (WebREPL 또는 USB)
# Thonny IDE 권장
```

### 3. ESP32-S3에서 직접 실행

#### Thonny IDE에서

1. Thonny 열기
2. 보드 선택 (우측 하단)
3. `test_kalman_micropython.py` 열기
4. **F5** 누르거나 Run 버튼 클릭

#### 시리얼 모니터에서

```bash
# putty, minicom, 또는 Python serial-monitor 사용
# 보드에서:
import test_kalman_micropython
test_kalman_micropython.run_all_tests()
```

## 테스트 내용

### 1. 1D Filter Tests (6개)
```
[OK] 1D Initialization              - 필터 초기화
[OK] 1D Constant Value Convergence  - 상수 신호 수렴
[OK] 1D Noise Reduction             - 노이즈 감소 효율
[OK] 1D Step Response               - 계단 응답 (0→10)
[OK] 1D Reset                       - 필터 리셋
[OK] 1D Gain Convergence            - 칼만 게인 수렴
```

### 2. 3D Filter Tests (3개)
```
[OK] 3D Initialization   - 3축 필터 초기화
[OK] 3D Filtering        - 3축 동시 필터링
[OK] 3D Independence     - 축 간 독립성
```

### 3. Adaptive Filter Tests (3개)
```
[OK] Adaptive Initialization     - 적응형 필터 초기화
[OK] Adaptive Noise Increase     - 노이즈 증가 적응
[OK] Adaptive Residuals          - 잔차 추적
```

### 4. Integration Tests (2개)
```
[OK] Gravity Measurement Filtering  - 중력 신호 필터링
[OK] Dynamic Acceleration Tracking  - 동적 가속도 추적
```

**총 14개 테스트 - 모두 통과**

## 실행 결과 예시

```
============================================================
KALMAN FILTER MICROPYTHON TEST SUITE
============================================================

1D Filter:
  [OK] 1D Initialization
  [OK] 1D Constant Value Convergence
  [OK] 1D Noise Reduction
  [OK] 1D Step Response
  [OK] 1D Reset
  [OK] 1D Gain Convergence

3D Filter:
  [OK] 3D Initialization
  [OK] 3D Filtering
  [OK] 3D Independence

Adaptive Filter:
  [OK] Adaptive Initialization
  [OK] Adaptive Noise Increase
  [OK] Adaptive Residuals

Integration Tests:
  [OK] Gravity Measurement Filtering
  [OK] Dynamic Acceleration Tracking

============================================================
RESULTS: 14/14 tests passed
============================================================

[SUCCESS] Kalman Filter ready for deployment
```

## 메모리 사용량

ESP32-S3에서의 예상 메모리 사용:

```
KalmanFilter1D:           ~100 bytes
KalmanFilter3D:           ~300 bytes (3개의 1D 필터)
AdaptiveKalmanFilter1D:   ~200 bytes + residuals buffer
```

ESP32-S3 총 메모리: **520 KB SRAM** - 여유 있음 ✓

## CPU 성능

ESP32-S3 @ 240MHz에서:

```
update() 한 번 실행:      ~1 ms
1000개 sample 처리:        ~1 second
```

**충분히 빠름** ✓

## 실제 센서와 통합

### EMG 신호 필터링 (Safety Mode)

```python
from firmware.sensor.emg import EMGSensor
from firmware.test_kalman_micropython import KalmanFilter1D
import time

emg = EMGSensor(pin=35)  # ADC pin
kf = KalmanFilter1D(process_variance=0.001, measurement_variance=0.3)

while True:
    raw = emg.read()           # 0-4095 ADC value
    filtered = kf.update(raw)  # 필터링된 신호
    print(f"EMG: {raw} -> {filtered:.2f}")
    time.sleep_ms(1)  # 1kHz sampling
```

### IMU 3축 필터링 (Control Mode)

```python
from firmware.sensor.imu import MPU6050
from firmware.test_kalman_micropython import KalmanFilter3D
import time

imu = MPU6050()
kf = KalmanFilter3D(process_variance=0.001, measurement_variance=0.2)

while True:
    ax, ay, az = imu.get_accel()
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    
    print(f"Accel: ({ax_f:.2f}, {ay_f:.2f}, {az_f:.2f}) m/s²")
    time.sleep_ms(10)  # 100Hz IMU
```

## 문제 해결

### 문제: 보드가 시리얼 포트로 인식되지 않음

```bash
# Windows: 드라이버 확인
# https://www.silabs.com/developers/mcu-programming-solutions/usb-to-uart-bridge-vcp-drivers

# Linux/Mac: 권한 확인
chmod 666 /dev/ttyUSB0
```

### 문제: ampy 업로드 실패

```bash
# 보드 재부팅
ampy --port COM5 repl
# REPL 진입 후 Ctrl+D로 부팅

# 또는 Thonny IDE 사용 (더 안정적)
```

### 문제: 메모리 부족 에러

```
MemoryError: memory allocation failed
```

→ 불필요한 변수 삭제, residuals buffer 크기 감소
```python
kf = AdaptiveKalmanFilter1D(
    base_measurement_variance=0.1,
    adaptation_rate=0.1,
)
kf.max_residuals = 20  # 기본값 50에서 감소
```

## 다음 단계

### 1. 실제 센서 데이터로 테스트

```python
# 보드에서:
import firmware.test_kalman_micropython as kf_test
import firmware.sensor.emg as emg_module

# EMG 센서 데이터 스트림 필터링
emg_sensor = emg_module.EMGSensor(pin=35)
kf_test.test_with_real_sensor(emg_sensor)
```

### 2. 성능 프로파일링

```python
import time
import firmware.test_kalman_micropython as kf

kf_inst = kf.KalmanFilter1D()
measurements = [5.0 + 0.5 * __import__('math').sin(i) for i in range(1000)]

start = time.ticks_ms()
for m in measurements:
    kf_inst.update(m)
elapsed = time.ticks_ms() - start

print(f"1000 updates: {elapsed}ms ({elapsed/1000:.3f}ms per update)")
```

### 3. OLED 디스플레이에 결과 표시

```python
from firmware.ui.oled import OLEDDisplay
import firmware.test_kalman_micropython as kf

oled = OLEDDisplay()
kf_inst = kf.KalmanFilter1D()

while True:
    raw = emg.read()
    filtered = kf_inst.update(raw)
    oled.display_text(f"Raw: {raw}")
    oled.display_text(f"Filtered: {filtered:.1f}")
```

## 참고 자료

- **MicroPython 공식**: https://micropython.org/
- **ESP32-S3 가이드**: https://docs.micropython.org/en/latest/esp32/quickref.html
- **Thonny IDE**: https://thonny.org/
- **Adafruit ampy**: https://github.com/adafruit/ampy

---
**테스트 상태**: ✅ 14/14 tests passing  
**보드 호환성**: ESP32-S3 (MicroPython 1.19+)  
**메모리**: ~300 bytes per 3D filter  
**성능**: ~1ms per update @ 240MHz
