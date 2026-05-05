# 택트 스위치 회로 (모드 전환)

**목적**: Safety Mode ↔ Control Mode 전환, 펌웨어 리셋

---

## 부품 목록

| 부품 | 모델 | 수량 | 비고 |
|------|------|------|------|
| 스위치 | 4핀 택트 스위치 | 1 | 푸시 버튼 |
| 저항 | 10kΩ 1/4W | 1 | 풀업 저항 (선택) |
| GPIO | GPIO21 | 1 | 디지털 입력 |

---

## 회로도 (내부 풀업 사용)

```
      ┌─→ GPIO21 (INPUT_PULLUP 펌웨어 설정)
    [SW]
      │
     GND

상태:
- SW 열림: GPIO21 = HIGH (3.3V, 내부 풀업)
- SW 닫힘: GPIO21 = LOW (0V)
```

## 회로도 (외부 풀업 저항 사용)

```
3.3V ──[10kΩ]──┬─→ GPIO21
               │
            [SW]
               │
              GND

상태:
- SW 열림: GPIO21 = HIGH (3.3V, 저항을 통해)
- SW 닫힘: GPIO21 = LOW (0V, GND로 직결)
```

---

## 4핀 택트 스위치 배치

```
   1 ─── 2  (한 쌍, 서로 연결됨)
   
   3 ─── 4  (다른 쌍, 서로 연결됨)

사용법:
1-3 쌍 사용: 1번 → GPIO21, 3번 → GND
또는
2-4 쌍 사용: 2번 → GPIO21, 4번 → GND
```

---

## 펌웨어 코드 (MicroPython)

### 방법 1: 내부 풀업 (권장)

```python
from machine import Pin
import time

# GPIO21을 INPUT_PULLUP으로 설정 (내부 풀업 활성화)
switch = Pin(21, Pin.IN, Pin.PULL_UP)

# 누르기 감지
while True:
    if switch.value() == 0:  # 버튼 눌림
        print("모드 전환!")
        time.sleep(0.3)  # 디바운싱 (300ms)
    time.sleep(0.1)
```

### 방법 2: 외부 풀업 (명시적)

```python
from machine import Pin
import time

# 외부 풀업 저항 사용
switch = Pin(21, Pin.IN)  # 또는 Pin.PULL_NONE

while True:
    if switch.value() == 0:  # 버튼 눌림 (GND로 연결)
        print("모드 전환!")
        time.sleep(0.3)  # 디바운싱
    time.sleep(0.1)
```

### 방법 3: 인터럽트 (이벤트 기반)

```python
from machine import Pin
import time

mode = "safety"

def mode_switch_callback(pin):
    global mode
    mode = "control" if mode == "safety" else "safety"
    print(f"모드 변경: {mode}")

# GPIO21을 인터럽트로 설정
switch = Pin(21, Pin.IN, Pin.PULL_UP)
switch.irq(trigger=Pin.IRQ_FALLING, handler=mode_switch_callback)

# 메인 루프
while True:
    print(f"현재 모드: {mode}")
    time.sleep(1)
```

---

## 디바운싱 (Debouncing)

**문제**: 스위치 접점이 떨려서 1번 누름이 여러 번으로 감지됨

**해결**:
```python
import time

last_press_time = 0
debounce_delay = 0.3  # 300ms

def check_switch():
    global last_press_time
    if switch.value() == 0:  # 버튼 눌림
        current_time = time.time()
        if current_time - last_press_time > debounce_delay:
            print("유효한 누르기!")
            last_press_time = current_time
        time.sleep(0.05)  # 약간 대기
```

---

## 모드 전환 로직 (Safety ↔ Control)

```python
from machine import Pin
import time

class ModeSwitch:
    def __init__(self, gpio_pin=21):
        self.switch = Pin(gpio_pin, Pin.IN, Pin.PULL_UP)
        self.mode = "safety"
        self.last_press = 0
        self.debounce_ms = 300
        
    def update(self):
        """메인 루프에서 호출"""
        if self.switch.value() == 0:  # 누름
            now = time.ticks_ms()
            if now - self.last_press > self.debounce_ms:
                self.mode = "control" if self.mode == "safety" else "safety"
                print(f"모드 변경: {self.mode}")
                self.last_press = now
            time.sleep(0.05)
    
    def get_mode(self):
        """현재 모드 반환"""
        return self.mode

# 사용 예
mode_switch = ModeSwitch(gpio_pin=21)

while True:
    mode_switch.update()
    print(f"Current: {mode_switch.get_mode()}")
    time.sleep(0.1)
```

---

## 배선 체크리스트

```
[ ] 택트 스위치 한 핀 → GPIO21
[ ] 택트 스위치 다른 핀 → GND
[ ] 풀업 저항 (선택): 3.3V ─[10kΩ]─ GPIO21
[ ] 펌웨어에서 INPUT_PULLUP 설정
[ ] 누를 때 GPIO21 = LOW (0V) 확인
```

---

## 상태 테스트 (Thonny REPL)

```python
from machine import Pin

sw = Pin(21, Pin.IN, Pin.PULL_UP)

# 누르기 전
print(sw.value())  # 출력: 1 (HIGH)

# 누르는 중
print(sw.value())  # 출력: 0 (LOW)
```

---

## 관련 문서

- `docs/02_HW/01_overall_circuit.md` — 전체 회로도
- `firmware/mode.py` — 모드 전환 펌웨어 (후속)
