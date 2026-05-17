# ESP32-S3 핀 설정 가이드

"invalid pin" 에러가 발생했을 때 해결하는 방법입니다.

## 🔴 에러 메시지

```
[ERROR] IMU test failed: invalid pin
```

## ✅ 원인 및 해결

### 1️⃣ 현재 핀 설정 확인

```python
# 기본값 (보드에 따라 다를 수 있음)
imu = MPU6050(sda_pin=21, scl_pin=22)
```

### 2️⃣ Seeed XIAO ESP32-S3 기본 I2C 핀

| 기능 | 핀 번호 | 핀 이름 |
|------|---------|--------|
| **SDA** | **21** | GPIO 21 |
| **SCL** | **22** | GPIO 22 |
| **GND** | GND | |
| **VCC** | 3.3V 또는 5V | |

**이 핀들을 사용하세요!**

## 🔧 테스트 코드로 올바른 핀 찾기

```python
from machine import I2C, Pin

# 가능한 I2C 포트 및 핀 조합 테스트
pin_combinations = [
    (21, 22),  # 기본값
    (20, 21),  # 대체 1
    (6, 7),    # 대체 2
    (8, 9),    # 대체 3
    (4, 5),    # 대체 4
]

for sda, scl in pin_combinations:
    try:
        i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)
        devices = i2c.scan()
        if devices:
            print(f"[OK] SDA={sda}, SCL={scl}: Found devices {devices}")
        else:
            print(f"[OK] SDA={sda}, SCL={scl}: Pins work, no devices")
    except ValueError as e:
        print(f"[FAIL] SDA={sda}, SCL={scl}: {e}")
    except Exception as e:
        print(f"[ERROR] SDA={sda}, SCL={scl}: {e}")
```

## 🎯 MPU6050 I2C 주소 확인

```python
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
devices = i2c.scan()

print(f"Found I2C devices: {devices}")

# 주소를 16진수로 변환
for addr in devices:
    print(f"  Device at: 0x{addr:02x}")

# MPU6050 기본 주소는 0x68
# MPU6050 AD0 핀이 HIGH면 0x69
```

**기대되는 출력:**
```
Found I2C devices: [104]
  Device at: 0x68
```

(104 = 0x68 in hex)

## 📋 연결 체크리스트

```
[ ] MPU6050 VCC → 3.3V 또는 5V
[ ] MPU6050 GND → GND
[ ] MPU6050 SDA → GPIO 21
[ ] MPU6050 SCL → GPIO 22
[ ] 풀업 저항 4.7kΩ (SDA, SCL) - 선택사항
[ ] USB 케이블로 ESP32-S3 전원 공급
```

## 🐛 일반적인 핀 설정 실수

### 실수 1️⃣: 핀 번호 바뀜

```python
# ❌ 틀림
imu = MPU6050(sda_pin=22, scl_pin=21)  # 반대!

# ✅ 올바름
imu = MPU6050(sda_pin=21, scl_pin=22)
```

### 실수 2️⃣: 존재하지 않는 핀

```python
# ❌ 틀림 (GPIO 50은 없음)
imu = MPU6050(sda_pin=50, scl_pin=51)

# ✅ 올바름
imu = MPU6050(sda_pin=21, scl_pin=22)
```

### 실수 3️⃣: 다른 기능에 사용 중인 핀

```python
# ❌ GPIO 21이 이미 다른 센서에 사용 중
from machine import Pin
button = Pin(21, Pin.IN)  # GPIO 21 사용 중
imu = MPU6050(sda_pin=21, scl_pin=22)  # 충돌!

# ✅ 대체 핀 사용
button = Pin(8, Pin.IN)
imu = MPU6050(sda_pin=21, scl_pin=22)
```

## 🛠️ 핀 설정 변경 방법

### 방법 1️⃣: 코드에서 직접 지정

```python
from firmware.sensor.imu import MPU6050

# 기본값 (21, 22) 대신 다른 핀 사용
imu = MPU6050(sda_pin=8, scl_pin=9)
```

### 방법 2️⃣: 자동 감지 (핀 스캔)

```python
from machine import I2C, Pin

# 사용 가능한 핀 찾기
test_pins = [(21, 22), (20, 21), (6, 7)]

for sda, scl in test_pins:
    try:
        i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)
        devices = i2c.scan()
        if 0x68 in devices:  # MPU6050 주소
            print(f"Found MPU6050 at SDA={sda}, SCL={scl}")
            break
    except:
        continue
```

## 📌 Seeed XIAO ESP32-S3 전체 핀맵

```
Front Side:
────────────────────────────
5V  GND  D0(GPIO8)
3V3 GND  D1(GPIO9)
────────────────────────────

Back Side:
GPIO 11  GPIO 12  GPIO 13
GPIO 10         GPIO 3 (RX)
GPIO 9   GPIO 4  GPIO 2 (TX)
GPIO 8   GPIO 5  GPIO 1
GPIO 7   GPIO 6
GPIO 21  GPIO 22 ← I2C (SDA/SCL) ← 기본값
GPIO 20  GPIO 19
GPIO 18  GPIO 17

I2C:
━━━━━━━━━━
SDA: GPIO 21
SCL: GPIO 22
━━━━━━━━━━
```

## ✅ 문제 해결 체크리스트

1. **연결 확인**
   - [ ] MPU6050 전원 (LED 켜있음?)
   - [ ] I2C 케이블 연결 확인
   - [ ] 핀 번호 맞는지 확인 (21=SDA, 22=SCL)

2. **핀 설정 확인**
   - [ ] `imu = MPU6050(sda_pin=21, scl_pin=22)` 사용
   - [ ] 다른 코드에서 GPIO 21/22 사용 중인지 확인

3. **I2C 주소 확인**
   ```python
   i2c = I2C(0, scl=Pin(22), sda=Pin(21))
   print(i2c.scan())  # [104] 나와야 함 (0x68)
   ```

4. **I2C 속도 조정**
   ```python
   # 느린 속도로 재시도
   imu = MPU6050(sda_pin=21, scl_pin=22)
   # 내부적으로 freq=100000으로 자동 재시도됨
   ```

## 🔗 참고 자료

- [Seeed XIAO ESP32-S3 공식 문서](https://wiki.seeedstudio.com/XIAO_ESP32S3_Getting_Started/)
- [MicroPython I2C API](https://docs.micropython.org/en/latest/library/machine.I2C.html)
- [MPU6050 데이터시트](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf)

## 💡 추가 팁

### 풀업 저항 필요한가?

ESP32-S3의 I2C 핀은 내부 풀업이 있지만, 장거리 케이블이나 여러 장치를 연결할 때는 외부 풀업 저항 (4.7kΩ) 추가:

```
3.3V
 │
 ├─ [4.7kΩ] ─ GPIO 21 (SDA)
 │
 └─ [4.7kΩ] ─ GPIO 22 (SCL)
```

### 디버깅용 I2C 스캔 스크립트

```python
from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

print("I2C Device Scanner")
print("─" * 40)

while True:
    devices = i2c.scan()
    if devices:
        print(f"Found devices: ", end="")
        for addr in devices:
            print(f"0x{addr:02x} ", end="")
        print()
    else:
        print("No devices found")
    
    time.sleep(1)
```

---

**마지막 업데이트**: 2026-05-12  
**호환 보드**: Seeed XIAO ESP32-S3  
**기본 I2C 핀**: GPIO 21 (SDA) / GPIO 22 (SCL)
