"""
RGB LED 색상 진단 도구
각 색상이 제대로 나오는지 확인합니다.

Thonny REPL에서 실행:
>>> exec(open('test_led_colors.py').read())
"""

import time
from machine import Pin, PWM
import config

print("=" * 70)
print("RGB LED Color Diagnostic Tool")
print("=" * 70)

# 핀 정보 확인
print(f"\n[Config] LED 핀 설정:")
print(f"  Red:   GPIO{config.LED_RED_PIN}")
print(f"  Green: GPIO{config.LED_GREEN_PIN}")
print(f"  Blue:  GPIO{config.LED_BLUE_PIN}")

# LED 초기화
try:
    red_pwm = PWM(Pin(config.LED_RED_PIN))
    green_pwm = PWM(Pin(config.LED_GREEN_PIN))
    blue_pwm = PWM(Pin(config.LED_BLUE_PIN))

    red_pwm.freq(1000)
    green_pwm.freq(1000)
    blue_pwm.freq(1000)

    print("\n✅ LED PWM 초기화 성공\n")
except Exception as e:
    print(f"\n❌ LED 초기화 실패: {e}\n")
    exit()

# 테스트 색상들
colors = {
    "OFF": (0, 0, 0),
    "RED": (1023, 0, 0),
    "GREEN": (0, 1023, 0),
    "BLUE": (0, 0, 1023),
    "YELLOW": (1023, 512, 0),
    "CYAN": (0, 1023, 1023),
    "MAGENTA": (1023, 0, 1023),
    "WHITE": (1023, 1023, 1023),
}

print("=" * 70)
print("색상 테스트 시작 (각 3초)\n")
print("예상 색상 | 실제 보이는 색상 | 상태")
print("-" * 70)

for color_name, (r, g, b) in colors.items():
    red_pwm.duty(r)
    green_pwm.duty(g)
    blue_pwm.duty(b)

    status = "✅" if (r, g, b) != (0, 0, 0) else "⭕"
    print(f"{color_name:8s} | {'    ' * 3:<12s} | {status} (대기 3초...)")
    time.sleep(3)

# 최종: LED OFF
red_pwm.duty(0)
green_pwm.duty(0)
blue_pwm.duty(0)

print("\n" + "=" * 70)
print("테스트 완료!")
print("=" * 70)

print("\n[진단 가이드]:")
print("❌ 색상이 안 나오는 경우:")
print("  1. 핀 연결 확인 (GPIO17/18/19 → LED R/G/B)")
print("  2. LED 극성 확인 (공통 캐소드/애노드)")
print("  3. config.py LED_RED/GREEN/BLUE_PIN 값 확인")
print("\n❌ 색상이 반대로 나오는 경우:")
print("  1. LED 극성이 반대일 수 있음 (공통 캐소드 ↔ 애노드)")
print("  2. config.py에서 핀 정의가 잘못되었을 수 있음")
print("\n✅ 모든 색상이 정상이면 LED 무선입니다!")

# 개별 핀 테스트 메뉴
print("\n" + "=" * 70)
print("개별 핀 테스트 (선택)")
print("=" * 70)
print("\nThonny REPL에서 다음 명령 실행:")
print("  빨강만: red_pwm.duty(1023); green_pwm.duty(0); blue_pwm.duty(0)")
print("  초록만: red_pwm.duty(0); green_pwm.duty(1023); blue_pwm.duty(0)")
print("  파랑만: red_pwm.duty(0); green_pwm.duty(0); blue_pwm.duty(1023)")
print("  끄기:   red_pwm.duty(0); green_pwm.duty(0); blue_pwm.duty(0)")
