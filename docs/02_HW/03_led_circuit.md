# LED 상태 표시 회로

**목적**: Safety Mode/Control Mode 상태, 피로도 수준(80%/95%) 시각적 피드백

---

## 부품 목록

| 부품 | 모델 | 수량 | 비고 |
|------|------|------|------|
| LED | 5mm 일반 LED | 1~3 | 적색/노랑/초록 또는 RGB |
| 저항 | 220Ω 1/4W | 1~3 | 전류 제한 |
| GPIO | GPIO18 | 1 | PWM 지원 |

---

## 회로도 (단색 LED)

```
GPIO18 ──[220Ω]──→ LED(+) ──→ LED(-) ──→ GND

동작:
- GPIO18 = HIGH → LED 점등
- GPIO18 = LOW → LED 소등
- PWM 사용 → 밝기 조절
```

## 회로도 (RGB LED, 공통 캐소드)

```
GPIO18 ──[220Ω]──→ LED R(+)  ──┐
GPIO17 ──[220Ω]──→ LED G(+)  ──┼─→ LED 공통(-) ──→ GND
GPIO16 ──[220Ω]──→ LED B(+)  ──┘
```

## 회로도 (RGB LED, 공통 애노드)

```
                  ┌── LED R(-) ──[220Ω]──→ GPIO18
3.3V ──→ LED(+) ──┼── LED G(-) ──[220Ω]──→ GPIO17
                  └── LED B(-) ──[220Ω]──→ GPIO16
```

---

## 저항값 계산

**단색 LED 기준**:
```
V_GPIO = 3.3V
V_LED = 2.0V (일반적인 적색 LED)
I_LED = 20mA (표준)

R = (V_GPIO - V_LED) / I_LED
  = (3.3 - 2.0) / 0.020
  = 65Ω

실제 사용: 220Ω (안정적, 밝기 ~ 5mA)
          100Ω (더 밝음, 밝기 ~ 10mA)
```

---

## 펌웨어 코드 (MicroPython)

### 단색 LED

```python
from machine import Pin, PWM

# GPIO18 디지털 출력
led = Pin(18, Pin.OUT)

# ON/OFF
led.on()
led.off()

# PWM으로 밝기 조절
led_pwm = PWM(Pin(18), freq=1000, duty=0)
led_pwm.duty(512)   # 50% 밝기
led_pwm.duty(1023)  # 100% 밝기
led_pwm.duty(0)     # OFF
```

### RGB LED (공통 캐소드)

```python
from machine import Pin, PWM

# GPIO 설정
r = PWM(Pin(18), freq=1000, duty=0)
g = PWM(Pin(17), freq=1000, duty=0)
b = PWM(Pin(16), freq=1000, duty=0)

def set_color(r_duty, g_duty, b_duty):
    r.duty(r_duty)
    g.duty(g_duty)
    b.duty(b_duty)

# 색상 설정
set_color(1023, 0, 0)      # 빨강
set_color(0, 1023, 0)      # 초록
set_color(0, 0, 1023)      # 파랑
set_color(1023, 1023, 0)   # 노랑 (빨강+초록)
set_color(0, 0, 0)         # 꺼짐
```

---

## 상태별 LED 패턴 (제안)

| 상태 | LED 색상 | 펌웨어 |
|------|---------|--------|
| Safety Mode (피로도 정상) | 초록 | `set_color(0, 1023, 0)` |
| Safety Mode (피로도 80%) | 노랑 | `set_color(1023, 1023, 0)` |
| Safety Mode (피로도 95%) | 빨강 | `set_color(1023, 0, 0)` |
| Control Mode 대기 | 파랑 | `set_color(0, 0, 1023)` |
| 오류/배터리 부족 | 빨강 깜빡임 | `toggle()` |

---

## 배선 체크리스트

```
[ ] LED(+) ← GPIO18 (220Ω 직렬)
[ ] LED(-) → GND
[ ] RGB인 경우 공통핀 명확 (애노드 or 캐소드)
[ ] 저항값 확인 (220Ω 또는 100Ω)
[ ] 극성 확인 (LED는 극성 있음)
```

---

## 관련 문서

- `docs/02_HW/01_overall_circuit.md` — 전체 회로도
- `firmware/ui/led.py` — LED 제어 펌웨어
