# IMU 센서 회로 (MPU6050)

**목적**: 6축 관성측정 (가속도 3축, 각속도 3축) → Control Mode 커서 이동

---

## 부품 목록

| 부품 | 모델 | 수량 | 비고 |
|------|------|------|------|
| IMU | GY-521 (MPU6050) | 1 | I2C 모듈 |
| GPIO | GPIO8 (SDA) | 1 | I2C 데이터 |
| GPIO | GPIO9 (SCL) | 1 | I2C 클럭 |

---

## 회로도

```
        ┌─────────────────┐
        │  GY-521 모듈    │
        │  (MPU6050)      │
        └────────┬────────┘
          6핀 커넥터
          │
          ├─ VCC ────────→ 3.3V
          ├─ GND ────────→ GND
          ├─ SDA ────────→ GPIO8 (I2C Data)
          ├─ SCL ────────→ GPIO9 (I2C Clock)
          ├─ XDA ────────→ (미사용)
          └─ XCL ────────→ (미사용)

I2C 풀업:
        ┌─ GPIO8 (SDA) ────┬─ MPU6050 SDA
        │                  ├─ OLED SDA (선택)
GPIO8 ──┤ (풀업 4.7kΩ)    │
        │                  └─ (모듈에 내장)
        │
        └─ GPIO9 (SCL) ────┬─ MPU6050 SCL
                           ├─ OLED SCL (선택)
GPIO9 ──┤ (풀업 4.7kΩ)    │
                           └─ (모듈에 내장)
```

---

## I2C 주소

```
MPU6050 (GY-521):
- I2C 주소: 0x68 (AD0 = GND, 기본값)
- 또는 0x69 (AD0 = 3.3V)

확인:
i2c.scan() 실행 → [0x68] 또는 [104] 출력
```

---

## 초기화 코드 (MicroPython)

### I2C 설정

```python
from machine import I2C, Pin

# I2C 버스 초기화 (GPIO8=SDA, GPIO9=SCL)
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)

# 연결된 I2C 기기 스캔
devices = i2c.scan()
print(f"I2C 디바이스: {devices}")

# 예상 출력:
# [0x68] 또는 [104]  → MPU6050 정상
# [0x68, 0x3C] 또는 [104, 60] → MPU6050 + OLED
```

### MPU6050 읽기

```python
# 기본 설정 (6g, ±250°/s)
def init_mpu6050():
    i2c.writeto(0x68, bytes([0x6B, 0x00]))  # Power on
    i2c.writeto(0x68, bytes([0x1A, 0x00]))  # DLPF off
    i2c.writeto(0x68, bytes([0x1B, 0x00]))  # Gyro ±250°/s
    i2c.writeto(0x68, bytes([0x1C, 0x00]))  # Accel ±2g

def read_mpu6050():
    """가속도 + 각속도 읽기"""
    # 레지스터 0x3B부터 14바이트 읽기
    data = i2c.readfrom(0x68, 14, stop=False)
    
    # 가속도 (6 bytes, 각 2bytes = 3축)
    accel_x = (data[0] << 8) | data[1]
    accel_y = (data[2] << 8) | data[3]
    accel_z = (data[4] << 8) | data[5]
    
    # 온도 (2 bytes, 확인용)
    temp = (data[6] << 8) | data[7]
    
    # 각속도 (6 bytes, 각 2bytes = 3축)
    gyro_x = (data[8] << 8) | data[9]
    gyro_y = (data[10] << 8) | data[11]
    gyro_z = (data[12] << 8) | data[13]
    
    return {
        'accel': (accel_x, accel_y, accel_z),
        'temp': temp,
        'gyro': (gyro_x, gyro_y, gyro_z)
    }
```

---

## 신호 범위

### 가속도 (Accel, ±2g)
```
정상 범위: -2g ~ +2g = -32768 ~ +32767 (16-bit)
지구 중력: 약 9.8 m/s² = 1g
- X축: 팔 좌우 방향
- Y축: 팔 앞뒤 방향  
- Z축: 상하 방향

예시:
정지 상태 (중력): Z축 ~ 16384 (1g), X/Y축 ~ 0
옆으로 숙임: X축 증가
앞으로 숙임: Y축 증가
```

### 각속도 (Gyro, ±250°/s)
```
정상 범위: -250°/s ~ +250°/s = -32768 ~ +32767 (16-bit)
- X축: 팔 회전 (롤/Roll)
- Y축: 팔 위아래 (피치/Pitch)
- Z축: 팔 좌우 회전 (요/Yaw)

예시:
정지 상태: 모두 0
회전 중: 해당 축 값 증가
```

---

## 펌웨어 코드 (IMUSensor 클래스)

```python
# firmware/sensor/imu.py

from machine import I2C, Pin
import math

class IMUSensor:
    """MPU6050 IMU 드라이버"""
    
    def __init__(self, i2c_id=0, sda_pin=8, scl_pin=9):
        self.i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.addr = 0x68
        self.init_mpu6050()
    
    def init_mpu6050(self):
        """MPU6050 초기화"""
        self.i2c.writeto(self.addr, bytes([0x6B, 0x00]))  # Power on
        self.i2c.writeto(self.addr, bytes([0x1A, 0x00]))  # DLPF off
        self.i2c.writeto(self.addr, bytes([0x1B, 0x00]))  # Gyro ±250°/s
        self.i2c.writeto(self.addr, bytes([0x1C, 0x00]))  # Accel ±2g
    
    def read_raw(self):
        """원본 16-bit 데이터 읽기"""
        data = self.i2c.readfrom(self.addr, 14)
        
        accel = [
            self._twos_complement(data[0], data[1]),
            self._twos_complement(data[2], data[3]),
            self._twos_complement(data[4], data[5])
        ]
        
        temp = self._twos_complement(data[6], data[7])
        
        gyro = [
            self._twos_complement(data[8], data[9]),
            self._twos_complement(data[10], data[11]),
            self._twos_complement(data[12], data[13])
        ]
        
        return {'accel': accel, 'temp': temp, 'gyro': gyro}
    
    def read_g(self):
        """가속도 (g 단위)"""
        raw = self.read_raw()
        return {
            'accel': [x / 16384.0 for x in raw['accel']],
            'gyro': [x / 131.0 for x in raw['gyro']]  # 250°/s 스케일
        }
    
    def read_angles(self):
        """Complementary Filter → pitch/roll 계산"""
        raw = self.read_raw()
        
        # 가속도 → pitch/roll
        ax, ay, az = [x / 16384.0 for x in raw['accel']]
        
        # 간단한 atan2 계산
        pitch = math.atan2(ax, math.sqrt(ay*ay + az*az)) * 180 / math.pi
        roll = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 180 / math.pi
        
        return {'pitch': pitch, 'roll': roll}
    
    @staticmethod
    def _twos_complement(msb, lsb):
        """16-bit 2의 보수 변환"""
        value = (msb << 8) | lsb
        if value & 0x8000:
            return value - 0x10000
        return value
    
    def test_sensor(self):
        """자가 테스트"""
        data = self.read_g()
        print(f"Accel: {data['accel']}")
        print(f"Gyro: {data['gyro']}")
```

---

## 테스트 코드 (Thonny REPL)

```python
from machine import I2C, Pin
import time

# I2C 초기화
i2c = I2C(0, scl=Pin(9), sda=Pin(8))

# 1단계: I2C 스캔
devices = i2c.scan()
print(f"I2C devices: {devices}")  # [0x68] 또는 [104]

# 2단계: MPU6050 파워 온
i2c.writeto(0x68, bytes([0x6B, 0x00]))

# 3단계: 데이터 읽기
for i in range(5):
    data = i2c.readfrom(0x68, 14)
    accel_x = (data[0] << 8) | data[1]
    print(f"AccelX: {accel_x}")
    time.sleep(0.5)
```

---

## 배선 체크리스트

```
[ ] MPU6050 VCC → 3.3V
[ ] MPU6050 GND → GND
[ ] MPU6050 SDA → GPIO8 (I2C 데이터)
[ ] MPU6050 SCL → GPIO9 (I2C 클럭)
[ ] I2C 스캔 (0x68 또는 0x69 감지?)
[ ] raw 데이터 읽기 확인
```

---

## 관련 파일

- `docs/02_HW/01_overall_circuit.md` — 전체 회로도
- `docs/02_HW/06_imu_circuit.md` — 이 파일
- `firmware/sensor/imu.py` — IMU 드라이버 (후속)
