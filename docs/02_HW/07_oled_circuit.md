# OLED 디스플레이 회로 (선택사항)

**목적**: 실시간 피로도, 모드, 배터리 상태 시각화 (0.96" SSD1306)

---

## 부품 목록

| 부품 | 모델 | 수량 | 비고 |
|------|------|------|------|
| OLED | 0.96" SSD1306 I2C | 1 | 128x64 해상도 (선택) |
| GPIO | GPIO8 (SDA) | 1 | I2C 데이터 (MPU6050과 공유) |
| GPIO | GPIO9 (SCL) | 1 | I2C 클럭 (MPU6050과 공유) |

---

## 회로도 (MPU6050과 I2C 공유)

```
        ┌──────────────────┐
        │  OLED SSD1306    │
        │  0.96" 128x64    │
        └────────┬─────────┘
          4핀 커넥터
          │
          ├─ VCC ────────→ 3.3V
          ├─ GND ────────→ GND
          ├─ SDA ────────→ GPIO8 (I2C Data, MPU6050과 공유)
          └─ SCL ────────→ GPIO9 (I2C Clock, MPU6050과 공유)

I2C 버스 구조 (MPU6050과 병렬):
                ┌─ GPIO8 (SDA)
GPIO8 (SDA) ────┼─ MPU6050 SDA
                ├─ OLED SDA
                └─ (풀업저항 4.7kΩ)

                ┌─ GPIO9 (SCL)
GPIO9 (SCL) ────┼─ MPU6050 SCL
                ├─ OLED SCL
                └─ (풀업저항 4.7kΩ)
```

---

## I2C 주소

```
OLED SSD1306:
- I2C 주소: 0x3C (고정, 주소 변경 불가)

I2C 스캔 예상 결과:
[0x68, 0x3C]  → MPU6050 (0x68) + OLED (0x3C) 모두 감지
```

---

## 초기화 코드 (MicroPython)

### I2C 버스 (MPU6050과 공유)

```python
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)

# 스캔
devices = i2c.scan()
print(f"I2C devices: {devices}")  # [0x68, 0x3C]
```

### SSD1306 드라이버 (MicroPython 내장)

```python
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

# I2C 초기화
i2c = I2C(0, scl=Pin(9), sda=Pin(8))

# OLED 초기화 (128x64 기본값)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 테스트
oled.text("Hello", 0, 0)     # (0,0) 위치에 텍스트
oled.show()                   # 디스플레이에 출력
```

---

## 펌웨어 코드 (OLED 표시)

```python
# firmware/ui/oled.py

from ssd1306 import SSD1306_I2C
from machine import I2C, Pin

class OLEDDisplay:
    """SSD1306 OLED 디스플레이"""
    
    def __init__(self, i2c_id=0, sda_pin=8, scl_pin=9):
        i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.display = SSD1306_I2C(128, 64, i2c, addr=0x3C)
    
    def show_mode(self, mode: str):
        """모드 표시 (Safety / Control)"""
        self.display.fill(0)  # 화면 지우기
        self.display.text(f"Mode: {mode}", 0, 0)
        self.display.show()
    
    def show_fatigue(self, level: int):
        """피로도 표시 (0~100%)"""
        self.display.fill(0)
        self.display.text(f"Fatigue: {level}%", 0, 0)
        self.display.show()
    
    def show_battery(self, voltage: float):
        """배터리 전압 표시"""
        self.display.fill(0)
        self.display.text(f"Battery: {voltage}V", 0, 0)
        self.display.show()
    
    def clear(self):
        """화면 지우기"""
        self.display.fill(0)
        self.display.show()
    
    def test(self):
        """자가 테스트"""
        self.display.fill(0)
        self.display.text("OLED Test OK", 0, 0)
        self.display.show()

# 사용 예
oled = OLEDDisplay()
oled.show_mode("Safety")
oled.show_fatigue(75)
```

---

## 표시 패턴 (예시)

### Safety Mode 메인 화면
```
┌──────────────────────┐
│ Safety Mode          │
│ Fatigue: 45%         │
│ ░░░░░░░░░░░░░░░░    │
└──────────────────────┘
```

### Control Mode 메인 화면
```
┌──────────────────────┐
│ Control Mode         │
│ Cursor Ready         │
│ Battery: 3.7V        │
└──────────────────────┘
```

### 알람 표시 (피로도 95%)
```
┌──────────────────────┐
│ ⚠️  FATIGUE 95%      │
│ Rest Now!            │
│ Motor: VIBRATING     │
└──────────────────────┘
```

---

## 테스트 코드 (Thonny REPL)

```python
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
import time

# I2C 초기화
i2c = I2C(0, scl=Pin(9), sda=Pin(8))

# OLED 초기화
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 1단계: 텍스트 표시
oled.text("Hello OLED", 0, 0)
oled.show()
time.sleep(2)

# 2단계: 여러 줄 표시
oled.fill(0)  # 화면 지우기
oled.text("Line 1", 0, 0)
oled.text("Line 2", 0, 10)
oled.text("Line 3", 0, 20)
oled.show()
time.sleep(2)

# 3단계: 선 그리기
oled.fill(0)
oled.hline(0, 10, 128, 1)  # 가로선
oled.vline(64, 0, 64, 1)   # 세로선
oled.show()
```

---

## 배선 체크리스트

```
[ ] OLED VCC → 3.3V
[ ] OLED GND → GND
[ ] OLED SDA → GPIO8 (MPU6050 SDA와 병렬)
[ ] OLED SCL → GPIO9 (MPU6050 SCL과 병렬)
[ ] I2C 스캔: [0x68, 0x3C] 감지?
[ ] 텍스트 표시 확인
```

---

## 관련 파일

- `docs/02_HW/01_overall_circuit.md` — 전체 회로도
- `docs/02_HW/06_imu_circuit.md` — IMU (I2C 공유)
- `firmware/ui/oled.py` — OLED 드라이버
