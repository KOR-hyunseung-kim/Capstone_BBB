# BBB 빠른 테스트 체크리스트 (5분)

> 펌웨어 배포 후 기본 동작 검증용 최소 테스트

---

## 🔌 사전 확인 (1분)

```
ESP32 USB 연결 → PC 인식
Thonny IDE 실행 → REPL 연결 확인
```

**확인 명령**:
```python
>>> import sys
>>> print(sys.version)
# MicroPython x.xx.x ... esp32-s3 ... 출력되면 OK
```

---

## 📁 파일 확인 (1분)

```python
>>> import os
>>> os.listdir()
# ['config.py', 'main.py', 'safety_mode.py', 'control_mode.py', 'sensor', 'ui', ...]
# 모두 있는지 확인
```

---

## ⚡ 부팅 테스트 (1분)

**Thonny REPL에서**:
```python
>>> exec(open('main.py').read())
```

**예상 출력**:
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

✅ 여기까지 출력되면 **부팅 성공**!

---

## 🔦 LED 테스트 (30초)

```python
>>> from ui.led import RGBLEDController
>>> from machine import Pin
>>> led = RGBLEDController(17, 18, 19)
>>> led.set_color("normal")    # 녹색
>>> # 2초 대기 확인
>>> led.set_color("warning")   # 황색
>>> # 2초 대기 확인
>>> led.set_color("critical")  # 적색
>>> # 2초 대기 확인
>>> led.off()                  # 꺼짐
```

**체크**:
- [ ] 녹색 점등
- [ ] 황색 점등
- [ ] 적색 점등
- [ ] 꺼짐

---

## 📳 모터 테스트 (30초)

```python
>>> from ui.motor import VibratorMotor
>>> motor = VibratorMotor(38)
>>> motor.single_pulse(100, 800)  # 진동 시작
>>> # 약 100ms 진동 감지
>>> motor.stop()  # 정지
```

**체크**:
- [ ] 진동 감지 (약 100ms)
- [ ] 정지 확인

---

## 📊 EMG 센서 테스트 (30초)

```python
>>> from sensor.emg import EMGSensor
>>> emg = EMGSensor(1)
>>> emg.test_sensor()
# EMG test: avg=XXXX (XXXXmV), range=XXXX-XXXX
```

**예상 범위**:
- ADC: 500~1500 (정상)
- mV: 400~1200 (정상)

**체크**:
- [ ] 값이 500~1500 범위 내?
  - Yes ✅ → EMG OK
  - No ❌ → 신호선 확인

---

## 🧭 IMU 센서 테스트 (30초)

```python
>>> from sensor.imu import MPU6050  # 또는 icm20602
>>> imu = MPU6050(sda_pin=8, scl_pin=9)
>>> ax, ay, az, gx, gy, gz, temp = imu.get_all()
>>> print(f"Accel: {ax:.2f}, {ay:.2f}, {az:.2f}")
>>> print(f"Gyro: {gx:.2f}, {gy:.2f}, {gz:.2f}")
>>> print(f"Temp: {temp:.1f}C")
```

**예상 값**:
- Accel: ax/ay ~0, az ~9.8 (정상 상태)
- Gyro: 모두 ~0 (움직이지 않을 때)
- Temp: 20~40°C

**체크**:
- [ ] 값이 정상 범위?
  - Yes ✅ → IMU OK
  - No ❌ → I2C 배선 확인 (GPIO8/9)

---

## 🔄 I2C 버스 확인

```python
>>> from machine import I2C, Pin
>>> i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
>>> devices = i2c.scan()
>>> print([hex(d) for d in devices])
# [0x68, 0x3c] 또는 [0x69, 0x3c] 출력
```

**예상**:
- `0x68` 또는 `0x69`: IMU (MPU6050 또는 ICM-20602)
- `0x3c`: OLED (연결한 경우)

**체크**:
- [ ] IMU 주소 감지?
  - Yes ✅ → I2C OK
  - No ❌ → GPIO8/9 배선 재확인

---

## 🚀 Safety Mode 간편 테스트 (2분)

```python
>>> from safety_mode import SafetyMode
>>> mode = SafetyMode()
>>> mode.calibrate(duration_sec=10)  # 10초 빠른 캘리브레이션
# [SafetyMode] Calibration starting (10s)...
# ... 10s ...
# [SafetyMode] Calibration complete. Baseline RMS: XXXX

>>> # 이제 근육 수축하지 않은 상태 유지
>>> status = mode.update()
>>> print(status['fatigue_level'])  # 'normal' 출력되어야 함
```

**체크**:
- [ ] Calibration 완료?
- [ ] fatigue_level이 'normal'?
- [ ] LED 녹색?

---

## 🎮 Control Mode 간편 테스트 (2분)

```python
>>> from control_mode import ControlMode
>>> mode = ControlMode()
>>> mode.calibrate(duration_sec=3)  # 3초 빠른 캘리브레이션
# [ControlMode] IMU calibration starting (3s)...
# ... 캘리브레이션 ...

>>> # 팔을 움직이지 않은 상태
>>> status = mode.update()
>>> print(f"Pitch: {status['pitch']:.1f}, Roll: {status['roll']:.1f}")
# Pitch: ~0, Roll: ~0 출력되어야 함
>>> print(f"Cursor: ({status['cursor_x']}, {status['cursor_y']})")
# Cursor: (512, 512) 출력되어야 함
```

**체크**:
- [ ] IMU 캘리브레이션 완료?
- [ ] Pitch/Roll ~0?
- [ ] Cursor 중앙 (512, 512)?

---

## ⚠️ 문제 진단 플로우

```
문제: LED가 켜지지 않음
  → GPIO17/18/19 배선 확인
  → PWM 테스트:
     >>> from machine import PWM, Pin
     >>> pwm = PWM(Pin(17))
     >>> pwm.duty(512)  # LED 점등 확인

문제: 모터가 진동하지 않음
  → GPIO38 배선 확인
  → 배터리 극성 확인 (매우 중요!)
  → MOSFET 핀 배치 확인 (1=G, 2=S, 3=D)

문제: EMG 값이 이상함 (0 또는 4095)
  → GPIO1 배선 확인
  → 신호선 스크린핑 추가
  → 센서 전원 3.3V 확인

문제: IMU가 인식되지 않음 (i2c.scan() 결과 [])
  → GPIO8(SDA), GPIO9(SCL) 배선 재확인
  → I2C 풀업 저항 확인 (모듈에 내장 확인)
  → 센서 전원 3.3V 확인
  → I2C 주소 확인 (MPU6050=0x68, ICM-20602=0x68 또는 0x69)
```

---

## 📋 최종 체크리스트

```
[ ] 파일 업로드 완료
[ ] 부팅 성공 (배너 출력)
[ ] LED 색상 변화 (녹→황→적)
[ ] 모터 진동 감지
[ ] EMG 센서 값 정상 (500~1500)
[ ] IMU 센서 값 정상 (Accel/Gyro 읽음)
[ ] I2C 버스에서 IMU 감지 (0x68 또는 0x69)
[ ] Safety Mode: 피로도 판정 작동
[ ] Control Mode: IMU 각도 계산 작동
```

---

## 🎉 모든 테스트 통과!

다음 단계:
1. **HW 최적화**
   - 배터리 용량 확인 (2시간 이상?)
   - 배선 보강 (스크린핑, 납땜 보강)

2. **소프트웨어 튜닝**
   - config.py 임계값 조정
   - Debug 플래그 비활성화 (배포용)

3. **WiFi/BLE 구현** (추후)
   - PC 데이터 수신
   - 외부 기기 제어

---
