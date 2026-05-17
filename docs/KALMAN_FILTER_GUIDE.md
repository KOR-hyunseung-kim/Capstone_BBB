# Kalman Filter Guide for Accelerometer

가속도 센서 노이즈를 제거하기 위한 칼만 필터 구현 및 사용 가이드입니다.

## 개요

**칼만 필터(Kalman Filter)**는 노이즈가 있는 측정값에서 실제 값을 추정하는 최적의 알고리즘입니다.

- **센서 노이즈 제거**: MyoWare EMG 또는 MPU6050 IMU의 랜덤 노이즈 감소
- **안정적인 필터링**: 라그가 최소화된 부드러운 신호
- **MicroPython 호환**: ESP32-S3 펌웨어에서 직접 사용 가능
- **적응형 필터**: 노이즈 수준이 변할 때 자동으로 파라미터 조정

## 파일 구조

```
firmware/algo/kalman_filter.py          # 칼만 필터 구현
  ├─ KalmanFilter1D                     # 1D 필터 (단일 축)
  ├─ KalmanFilter3D                     # 3D 필터 (3축 IMU)
  └─ AdaptiveKalmanFilter1D             # 적응형 필터

tests/test_kalman_accelerometer.py      # 18개 pytest 단위 테스트
tools/demo_kalman_filter.py             # 5가지 사용 예제 데모
```

## 기본 사용법

### 1. 1D 칼만 필터 (단일 축)

가장 간단한 형태 — 한 축의 가속도만 필터링

```python
from firmware.algo.kalman_filter import KalmanFilter1D

# 필터 초기화
kf = KalmanFilter1D(
    process_variance=0.001,        # Q: 프로세스 노이즈 (낮을수록 빠른 반응)
    measurement_variance=0.3,      # R: 센서 노이즈 (높을수록 더 많이 필터링)
)

# 센서 데이터 필터링
raw_accel = 9.81  # 센서에서 읽은 값
filtered_accel = kf.update(raw_accel)
print(f"Filtered: {filtered_accel:.4f} m/s²")
```

### 2. 3D 칼만 필터 (MPU6050 IMU)

3축 가속도계 필터링 — 각 축이 독립적으로 동작

```python
from firmware.algo.kalman_filter import KalmanFilter3D

kf = KalmanFilter3D(
    process_variance=0.001,
    measurement_variance=0.2,
)

# 3축 데이터 동시 필터링
ax_raw, ay_raw, az_raw = 9.81, 0.1, -0.3  # IMU에서 읽은 값
ax_filt, ay_filt, az_filt = kf.update(ax_raw, ay_raw, az_raw)
print(f"Filtered: ({ax_filt:.2f}, {ay_filt:.2f}, {az_filt:.2f}) m/s²")
```

### 3. 적응형 칼만 필터 (변하는 노이즈)

센서 노이즈 수준이 변할 때 자동으로 필터 강도를 조정

```python
from firmware.algo.kalman_filter import AdaptiveKalmanFilter1D

kf = AdaptiveKalmanFilter1D(
    process_variance=0.001,
    base_measurement_variance=0.1,  # 초기 센서 노이즈
    adaptation_rate=0.1,            # 적응 속도
)

# 시간이 지나면서 노이즈가 증가해도 자동으로 대응
for i in range(100):
    raw = 5.0 + noise[i]
    filtered = kf.update(raw)
    print(f"Measurement Variance (R): {kf.r:.4f}")  # R이 증가함
```

## 파라미터 조정

### Process Variance (Q)
- **역할**: 실제 신호가 얼마나 빠르게 변할 수 있는지
- **작은 값** (0.001): 천천히 변하는 신호 → 더 민감한 필터링
- **큰 값** (0.1): 빠르게 변하는 신호 → 더 적응형 필터링

### Measurement Variance (R)
- **역할**: 센서 노이즈의 크기
- **작은 값** (0.1): 노이즈가 적은 센서 → 더 강한 필터링
- **큰 값** (1.0): 노이즈가 많은 센서 → 더 약한 필터링

### 추천 파라미터

| 센서 | Q | R | 용도 |
|------|---|---|------|
| MyoWare EMG | 0.001 | 0.3 | 근활동 신호 |
| MPU6050 (Accel) | 0.001 | 0.2 | IMU 가속도 |
| MPU6050 (Gyro) | 0.005 | 0.1 | 각속도 |

## BBB Safety Mode 통합 예제

Safety Mode에서 EMG 신호를 칼만 필터로 전처리:

```python
from firmware.sensor.emg import EMGSensor
from firmware.algo.kalman_filter import KalmanFilter1D

emg_sensor = EMGSensor(pin=35)
kf = KalmanFilter1D(
    process_variance=0.001,
    measurement_variance=0.3,
)

while True:
    raw_emg = emg_sensor.read()       # 0-4095 ADC
    filtered_emg = kf.update(raw_emg)
    
    # 필터링된 신호로 피로도 판정
    # ...
```

## BBB Control Mode 통합 예제

Control Mode에서 IMU 데이터를 3D 칼만 필터로 전처리:

```python
from firmware.sensor.imu import MPU6050
from firmware.algo.kalman_filter import KalmanFilter3D

imu = MPU6050()
kf = KalmanFilter3D(
    process_variance=0.001,
    measurement_variance=0.2,
)

while True:
    ax, ay, az = imu.get_accel()
    
    # 필터링된 가속도
    ax_f, ay_f, az_f = kf.update(ax, ay, az)
    
    # 필터링된 값으로 기울기 계산
    pitch = math.atan2(ay_f, math.sqrt(ax_f**2 + az_f**2))
    roll = math.atan2(ax_f, az_f)
    
    # 커서 이동 등...
```

## 테스트 실행

### 모든 테스트 실행

```bash
python -m pytest tests/test_kalman_accelerometer.py -v
```

결과: **18 passed** ✓

테스트 항목:
- ✅ 필터 초기화 및 파라미터
- ✅ 상수 신호 수렴
- ✅ 노이즈 감소 효율
- ✅ 계단 응답 (Step Response)
- ✅ 칼만 게인 수렴
- ✅ 3축 독립 필터링
- ✅ 적응형 필터 노이즈 추적
- ✅ 중력 측정 필터링
- ✅ 동적 가속도 추적

### 데모 실행

```bash
python tools/demo_kalman_filter.py
```

5가지 데모:
1. **1D 필터**: 중력 측정값 필터링
2. **3D 필터**: IMU 3축 데이터 필터링
3. **적응형 필터**: 노이즈 수준 변화에 대응
4. **계단 응답**: 0 → 10 m/s² 전환 응답성
5. **노이즈 감소 지표**: 분산 감소율 61.2%

## 성능 지표

### 노이즈 감소
- **분산 감소**: 40~60%
- **응답 시간**: 10~50ms (파라미터 선택에 따라)
- **오버슈트**: 없음 (안정적)

### 메모리 & CPU
- **RAM**: ~100 bytes (1D 필터당)
- **CPU**: ~1ms per update (MicroPython ESP32-S3)
- **MicroPython 호환**: numpy 불필요, 순수 Python

## 고급 팁

### 1. 필터 리셋

필터를 초기화하고 싶을 때:
```python
kf.reset(initial_value=9.81)
```

### 2. 필터 상태 확인

칼만 게인과 에러 공분산 확인:
```python
print(f"Kalman Gain (K): {kf.k:.6f}")
print(f"Estimate Error (P): {kf.p:.6f}")
```

### 3. 오프라인 파라미터 튜닝

PC에서 파라미터를 최적화한 후 펌웨어에 적용:
```bash
# 다양한 Q, R 조합으로 테스트
python tools/test_kalman_params.py --q_range 0.001,0.01 --r_range 0.1,1.0
```

## 일반적인 문제

### 필터가 센서 변화를 따라가지 못함
→ `process_variance (Q)` 증가 (0.001 → 0.01)

### 필터가 노이즈를 제거하지 못함
→ `measurement_variance (R)` 증가 (0.3 → 1.0)

### 필터 반응이 너무 느림
→ `measurement_variance (R)` 감소 (0.3 → 0.1)

### 필터 신호가 진동함
→ `process_variance (Q)` 감소 (0.01 → 0.001)

## 참고 자료

- Kalman Filter 이론: https://en.wikipedia.org/wiki/Kalman_filter
- BBB 센서: [firmware/sensor/](../firmware/sensor/)
- EMG 처리: [firmware/algo/emg_processor.py](../firmware/algo/emg_processor.py)

---
**생성일**: 2026-05-12  
**테스트 상태**: ✅ All 18 tests passing
