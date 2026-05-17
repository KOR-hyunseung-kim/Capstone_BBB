# "invalid pin" 에러 해결 가이드

ESP32-S3에서 `[ERROR] IMU test failed: invalid pin` 에러가 발생했을 때의 해결 방법입니다.

## 🚨 에러 발생 시

```
[ERROR] IMU test failed: invalid pin
[ERROR] Pin configuration error: ...
```

## ✅ 단계별 해결

### 1단계: I2C 핀 진단 (ESP32-S3에서)

**Thonny IDE 또는 REPL에서:**

```python
import test_kalman_micropython

# 자동 I2C 진단 실행
test_kalman_micropython.diagnose_i2c_pins()
```

**예상 출력:**
```
======================================================================
I2C PIN DIAGNOSIS
======================================================================

Testing I2C pin combinations...
----------------------------------------------------------------------
  SDA=21 SCL=22 (Default (GPIO21=SDA, GPIO22=SCL)): [SUCCESS] - Found: ['0x68'] ← MPU6050 detected!
  SDA=20 SCL=21 (Alternative 1                 ): [INVALID PIN]
  SDA= 6 SCL= 7 (Alternative 2                 ): [INVALID PIN]
  SDA= 8 SCL= 9 (Alternative 3                 ): [INVALID PIN]
  SDA= 4 SCL= 5 (Alternative 4                 ): [INVALID PIN]
----------------------------------------------------------------------

[SUCCESS] MPU6050 found at 0x68!
Use: imu = MPU6050(sda_pin=21, scl_pin=22)
```

### 2단계: MPU6050 물리적 연결 확인

```
Seeed XIAO ESP32-S3   MPU6050
───────────────────   ────────
   5V 또는 3.3V  ───→  VCC
   GND          ───→  GND
   GPIO 21 (D7) ───→  SDA (Pin 12)
   GPIO 22 (D8) ───→  SCL (Pin 13)
```

**체크리스트:**
- [ ] MPU6050에 전원이 공급되는가? (보드 위의 LED가 켜있는가?)
- [ ] 케이블이 올바르게 연결되었는가?
- [ ] 핀 번호가 맞는가? (21=SDA, 22=SCL)
- [ ] 느슨한 연결은 없는가?

### 3단계: 올바른 핀으로 테스트 실행

```python
import test_kalman_micropython

# 기본 핀으로 실행
test_kalman_micropython.test_imu_kalman_realtime(
    duration=30,      # 30초 동안
    sample_rate=50,   # 50Hz
    sda_pin=21,       # GPIO 21
    scl_pin=22        # GPIO 22
)
```

## 🔍 상세 문제 해결

### 문제 1: "invalid pin" 계속 발생

```
→ 진단 함수 결과 확인:
  1. diagnose_i2c_pins() 실행
  2. MPU6050 found at 0x68! 메시지 있는지 확인
  3. 없으면 → 물리적 연결 재확인
```

### 문제 2: MPU6050을 찾을 수 없음 (0x68 없음)

```python
# 수동 I2C 스캔
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
devices = i2c.scan()
print(f"Found devices: {devices}")

# 출력 분석:
# [] 또는 빈 리스트 → 센서 찾을 수 없음
# [104] → 0x68 (MPU6050) 찾음
# [다른 숫자] → 다른 주소에 센서가 있음
```

**해결 방법:**
```
[ ] MPU6050 전원 연결 확인 (3.3V, 최소 100mA)
[ ] I2C 케이블 연결 상태 재확인
[ ] 풀업 저항 추가 (4.7kΩ, SDA/SCL 각각)
[ ] 핀 단락(short circuit) 확인
[ ] 센서 교체 시도
```

### 문제 3: 다른 주소의 센서가 감지됨 (예: 0x69)

```
→ MPU6050 AD0 핀 설정
  - GND 연결 → 0x68 (기본)
  - VCC 연결 → 0x69 (선택사항)
```

## 🛠️ 고급 진단: 마스터 테스트 스크립트

```python
from machine import I2C, Pin, machine
import time

print("=" * 70)
print("ADVANCED I2C DIAGNOSTIC")
print("=" * 70)

# 1. 보드 정보
print("\n[1] Board Information:")
print(f"    Chip: {machine.unique_id()}")

# 2. 핀 상태 확인
print("\n[2] GPIO 21/22 Status:")
try:
    sda_pin = Pin(21, Pin.IN)
    scl_pin = Pin(22, Pin.IN)
    print(f"    GPIO 21 (SDA): readable")
    print(f"    GPIO 22 (SCL): readable")
except Exception as e:
    print(f"    ERROR: {e}")

# 3. I2C 통신 테스트
print("\n[3] I2C Communication Test:")
try:
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    devices = i2c.scan()
    
    if not devices:
        print("    No devices found")
    else:
        print(f"    Found devices: {devices}")
        
        # 0x68 (MPU6050) 테스트
        if 0x68 in devices:
            try:
                # WHO_AM_I 레지스터 읽기 (주소: 0x75)
                whoami = i2c.readfrom_mem(0x68, 0x75, 1)[0]
                print(f"    MPU6050 WHO_AM_I: 0x{whoami:02x} (expected 0x71)")
                
                if whoami == 0x71:
                    print("    ✓ MPU6050 정상!")
                else:
                    print("    ✗ 센서 응답이 이상함")
            except Exception as e:
                print(f"    ✗ 센서 읽기 실패: {e}")
        else:
            print(f"    MPU6050 (0x68) not found at expected address")
            
except Exception as e:
    print(f"    I2C Error: {e}")

print("\n" + "=" * 70)
```

## 📋 최종 체크리스트

### 하드웨어 체크
```
[ ] ESP32-S3 보드가 정상 부팅하는가?
[ ] USB 케이블이 안전하게 연결되었는가?
[ ] MPU6050의 LED가 켜있는가?
[ ] I2C 케이블이 느슨하지 않은가?
[ ] 핀 연결이 정확한가? (21=SDA, 22=SCL)
```

### 소프트웨어 체크
```
[ ] MicroPython이 최신 버전인가?
[ ] firmware/sensor/imu.py가 업로드되었는가?
[ ] firmware/algo/kalman_filter.py가 업로드되었는가?
[ ] test_kalman_micropython.py가 업로드되었는가?
[ ] diagnose_i2c_pins() 실행했는가?
```

### 테스트 순서
```
1. diagnose_i2c_pins() 실행
2. 결과에서 "SUCCESS" 또는 "MPU6050 detected!" 확인
3. test_imu_kalman_realtime() 실행
4. 로그 출력이 시작되는지 확인
```

## 🔗 추가 도움말

| 문제 | 해결책 |
|------|--------|
| 진단 중 "no module named 'imu'" | 경로 추가: `sys.path.insert(0, '/firmware')` |
| I2C 속도 에러 | 속도 감소: `freq=100000` 사용 |
| 센서가 응답하지 않음 | 풀업 저항 추가 (4.7kΩ) |
| 주기적인 연결 끊김 | 케이블 품질 확인, 길이 단축 |

## 🆘 여전히 문제가 있다면?

다음 정보와 함께 확인하세요:

1. **진단 결과**
   ```python
   diagnose_i2c_pins()
   ```
   의 전체 출력

2. **보드 정보**
   ```python
   from machine import unique_id
   print(unique_id())
   ```

3. **시스템 로그** (Thonny 오른쪽 패널)

---

**마지막 업데이트**: 2026-05-12  
**호환성**: Seeed XIAO ESP32-S3 + MPU6050  
**MicroPython 버전**: 1.19+
