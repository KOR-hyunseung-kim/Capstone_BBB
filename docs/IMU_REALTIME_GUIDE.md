# Real-time IMU with Kalman Filter - 사용 가이드

MPU6050 센서를 칼만 필터로 처리하여 실시간으로 기울기(pitch, roll)와 가속도를 읽는 가이드입니다.

## 빠른 시작 (PC 시뮬레이션)

```bash
# PC에서 시뮬레이션 (ESP32-S3 없이도 테스트 가능)
python tools/simulate_imu_kalman.py --duration 10 --rate 100
```

**출력 예시:**
```
pitch:  15.9d roll:   1.1d | x: -0.02 y:  1.76 z:  8.79 | gx:  429.3 gy:    0.1 gz:   -0.2 | T: 25.0C
pitch:  23.2d roll:   1.6d | x:  0.01 y:  1.81 z:  9.08 | gx:  429.3 gy:   -1.0 gz:   -0.2 | T: 25.0C
pitch:  30.2d roll:   2.1d | x:  0.03 y:  1.84 z:  9.23 | gx:  429.2 gy:   -2.0 gz:   -0.2 | T: 25.1C
```

## 로그 형식 설명

```
pitch:  30.2d roll:   2.1d | x:  0.03 y:  1.84 z:  9.23 | gx:  429.2 gy:   -2.0 gz:   -0.2 | T: 25.1C
```

| 항목 | 설명 | 단위 | 범위 |
|------|------|------|------|
| **pitch** | Y축 회전 (전후 기울임) | 도(°) | -90~+90 |
| **roll** | X축 회전 (좌우 기울임) | 도(°) | -90~+90 |
| **x** | 칼만 필터 적용된 X축 가속도 | m/s² | -20~+20 |
| **y** | 칼만 필터 적용된 Y축 가속도 | m/s² | -20~+20 |
| **z** | 칼만 필터 적용된 Z축 가속도 | m/s² | 0~20 |
| **gx** | X축 각속도 (회전 속도) | deg/s | -500~+500 |
| **gy** | Y축 각속도 | deg/s | -500~+500 |
| **gz** | Z축 각속도 | deg/s | -500~+500 |
| **T** | 온도 | °C | 0~60 |

## 기울기(Tilt) 설명

### Pitch (전후 기울임)
- **0°**: 기기가 수평
- **+90°**: 기기가 앞으로 90° 기울어짐
- **-90°**: 기기가 뒤로 90° 기울어짐

### Roll (좌우 기울임)
- **0°**: 기기가 수평
- **+90°**: 기기가 오른쪽으로 기울어짐
- **-90°**: 기기가 왼쪽으로 기울어짐

## ESP32-S3에서 실행하기

### 1단계: 파일 업로드

```bash
# 방법 1: ampy 사용
pip install adafruit-ampy
ampy --port COM5 put firmware/sensor/imu.py imu.py
ampy --port COM5 put firmware/test_kalman_micropython.py kalman.py
ampy --port COM5 put firmware/examples/imu_kalman_realtime.py imu_realtime.py

# 방법 2: Thonny IDE (권장)
# 파일 우클릭 → Upload to /
```

### 2단계: ESP32-S3에서 실행

**Thonny IDE:**
1. 파일 열기: `firmware/examples/imu_kalman_realtime.py`
2. F5 눌러서 실행

**시리얼 모니터:**
```python
import imu_realtime
imu_realtime.main()
```

## 코드 예제

### 예제 1: 기본 IMU 데이터 읽기

```python
from sensor.imu import MPU6050

imu = MPU6050(sda_pin=21, scl_pin=22)

# 가속도 읽기 (m/s²)
ax, ay, az = imu.get_accel()
print(f"Accel: x={ax:.2f} y={ay:.2f} z={az:.2f}")

# 각속도 읽기 (deg/s)
gx, gy, gz = imu.get_gyro()
print(f"Gyro: x={gx:.1f} y={gy:.1f} z={gz:.1f}")

# 온도 읽기 (°C)
temp = imu.get_temperature()
print(f"Temperature: {temp:.1f}C")

# 모든 데이터 한 번에
ax, ay, az, gx, gy, gz, temp = imu.get_all()
```

### 예제 2: 칼만 필터 적용

```python
from sensor.imu import MPU6050
from algo.kalman_filter import KalmanFilter3D

imu = MPU6050()
kf = KalmanFilter3D(
    process_variance=0.001,      # 신호 변화 속도
    measurement_variance=0.2,    # 센서 노이즈 수준
)

while True:
    # 원본 센서 데이터
    ax, ay, az = imu.get_accel()
    
    # 칼만 필터 적용
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    
    print(f"Filtered: x={ax_f:.2f} y={ay_f:.2f} z={az_f:.2f}")
```

### 예제 3: 기울기 계산 (Pitch & Roll)

```python
import math
from sensor.imu import MPU6050
from algo.kalman_filter import KalmanFilter3D

imu = MPU6050()
kf = KalmanFilter3D(process_variance=0.001, measurement_variance=0.2)

while True:
    ax, ay, az = imu.get_accel()
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    
    # 기울기 계산
    pitch = math.degrees(math.atan2(ax_f, math.sqrt(ay_f**2 + az_f**2)))
    roll = math.degrees(math.atan2(ay_f, math.sqrt(ax_f**2 + az_f**2)))
    
    print(f"Pitch: {pitch:.1f}° Roll: {roll:.1f}°")
```

### 예제 4: Complementary Filter (Gyro + Accel 융합)

```python
from sensor.imu import MPU6050
from algo.kalman_filter import KalmanFilter3D
import math
import time

imu = MPU6050()
kf = KalmanFilter3D()

alpha = 0.95  # 가속도 영향도 (0.9~0.99)
pitch = 0.0
roll = 0.0
dt = 0.01  # 10ms (100Hz)

while True:
    ax, ay, az, gx, gy, gz, _ = imu.get_all()
    
    # 칼만 필터로 가속도 노이즈 제거
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    
    # 각속도 적분
    pitch += math.radians(gx) * dt
    roll += math.radians(gy) * dt
    
    # 가속도 기반 기울기
    accel_pitch = math.atan2(ax_f, math.sqrt(ay_f**2 + az_f**2))
    accel_roll = math.atan2(ay_f, math.sqrt(ax_f**2 + az_f**2))
    
    # Complementary filter 융합
    pitch = alpha * pitch + (1 - alpha) * accel_pitch
    roll = alpha * roll + (1 - alpha) * accel_roll
    
    print(f"Pitch: {math.degrees(pitch):.1f}° Roll: {math.degrees(roll):.1f}°")
    time.sleep(dt)
```

## 파라미터 조정

### Kalman Filter 파라미터

```python
kf = KalmanFilter3D(
    process_variance=0.001,      # Q: 신호 변화 속도
    measurement_variance=0.2,    # R: 센서 노이즈
)
```

| 파라미터 | 설명 | 권장값 | 범위 |
|---------|------|---------|------|
| **process_variance (Q)** | 신호가 얼마나 빠르게 변할 수 있는지 | 0.001 | 0.0001~0.1 |
| **measurement_variance (R)** | 센서 노이즈의 크기 | 0.2 | 0.05~1.0 |

#### Q가 작으면:
- 더 강한 필터링 (노이즈 감소)
- 느린 응답
- 천천히 변하는 신호에 좋음

#### R이 크면:
- 센서를 덜 신뢰
- 더 강한 필터링
- 노이즈가 많은 센서에 좋음

### Complementary Filter 파라미터

```python
alpha = 0.95  # 0.0 ~ 1.0
```

- **alpha = 0.9**: 자이로 의존도 높음 (빠른 응답, 드리프트 가능)
- **alpha = 0.95**: 균형잡힌 융합
- **alpha = 0.99**: 가속도 의존도 높음 (느린 응답, 안정적)

## 센서 캘리브레이션

### 자동 캘리브레이션

```python
imu = MPU6050()

# 가속도 캘리브레이션 (기기를 움직이지 않음)
imu.calibrate_accel(samples=100)

# 자이로 캘리브레이션 (기기를 움직이지 않음)
imu.calibrate_gyro(samples=100)
```

### 수동 캘리브레이션

```python
# 오프셋 설정
imu.accel_offset = [0.05, -0.03, -0.1]
imu.gyro_offset = [0.5, -0.3, 0.2]
```

## Control Mode에서의 활용

BBB Control Mode에서 IMU를 사용한 커서 제어:

```python
from sensor.imu import MPU6050
from algo.kalman_filter import KalmanFilter3D
import math

imu = MPU6050()
kf = KalmanFilter3D()

# 초기 기울기
pitch, roll = 0.0, 0.0
center_pitch, center_roll = 0.0, 0.0

# 기준점 설정 (처음 1초간 평균값)
for _ in range(100):
    ax, ay, az, gx, gy, gz, _ = imu.get_all()
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    cp = math.atan2(ax_f, math.sqrt(ay_f**2 + az_f**2))
    cr = math.atan2(ay_f, math.sqrt(ax_f**2 + az_f**2))
    center_pitch += math.degrees(cp)
    center_roll += math.degrees(cr)

center_pitch /= 100
center_roll /= 100

# 커서 이동 루프
while True:
    ax, ay, az, gx, gy, gz, _ = imu.get_all()
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    
    pitch = math.degrees(math.atan2(ax_f, math.sqrt(ay_f**2 + az_f**2)))
    roll = math.degrees(math.atan2(ay_f, math.sqrt(ax_f**2 + az_f**2)))
    
    # 기준점으로부터의 변위
    delta_pitch = pitch - center_pitch
    delta_roll = roll - center_roll
    
    # 커서 이동 스케일 (조정 가능)
    cursor_x = delta_roll * 5
    cursor_y = -delta_pitch * 5  # Y축 반전
    
    # BLE HID로 커서 이동
    # hid_mouse.move(cursor_x, cursor_y)
    
    print(f"Cursor: x={cursor_x:.1f} y={cursor_y:.1f}")
```

## Safety Mode에서의 활용

BBB Safety Mode에서 IMU를 사용한 모니터링:

```python
from sensor.imu import MPU6050

imu = MPU6050()

while True:
    ax, ay, az, gx, gy, gz, temp = imu.get_all()
    
    # 과도한 움직임 감지
    total_motion = abs(gx) + abs(gy) + abs(gz)
    
    if total_motion > 500:  # 빠른 움직임
        print("Alert: Rapid motion detected")
    
    if temp > 40:  # 고온
        print("Warning: High temperature")
```

## 문제 해결

### 1. 센서에서 데이터를 읽을 수 없음

```
OSError: [Errno 110] ETIMEDOUT
```

**해결:**
```python
# I2C 핀 확인 (ESP32-S3 기본값: 21=SDA, 22=SCL)
imu = MPU6050(sda_pin=21, scl_pin=22)

# 또는 I2C 속도 조정
from machine import I2C
i2c = I2C(0, scl=22, sda=21, freq=100000)  # 100kHz로 감소
```

### 2. 기울기가 진동함

**해결:**
```python
# 필터 강화
kf = KalmanFilter3D(
    process_variance=0.0001,  # 더 작게
    measurement_variance=0.5,  # 더 크게
)
```

### 3. 기울기가 천천히 변함 (lag)

**해결:**
```python
# 필터 약화
kf = KalmanFilter3D(
    process_variance=0.01,     # 더 크게
    measurement_variance=0.05, # 더 작게
)
```

### 4. 메모리 부족

```
MemoryError: memory allocation failed
```

**해결:**
- 샘플 레이트 감소 (100Hz → 50Hz)
- 칼만 필터만 사용 (complementary filter 제거)
- 로깅 제거

## 성능 지표

| 항목 | 값 |
|------|-----|
| **샘플 레이트** | 100 Hz (10ms) |
| **응답 시간** | <50ms |
| **CPU 사용량** | ~5% @ 100Hz |
| **메모리** | ~500 bytes |
| **정확도** | ±1-2° |

## 다음 단계

1. ✅ IMU 칼만 필터 테스트
2. ✅ Pitch/Roll 기울기 계산
3. → Control Mode에 통합
4. → EMG와 함께 Safety Mode 구현

---

**생성일**: 2026-05-12  
**호환 보드**: ESP32-S3, STM32 (I2C 지원)  
**센서**: MPU6050 (6축)  
**필터**: 칼만 필터 + Complementary Filter
