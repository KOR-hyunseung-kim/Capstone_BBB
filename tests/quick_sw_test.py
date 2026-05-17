from machine import Pin
import time

# GPIO21 입력 설정
switch = Pin(4, Pin.IN)

print("스위치 상태 모니터링 (누르면 변화를 봐주세요)")
print("=" * 40)

while True:
    val = switch.value()
    print(f"GPIO21: {val}")  # 0 또는 1 출력
    time.sleep(0.2)
