from machine import Pin

# GPIO 설정
r = Pin(38, Pin.OUT)
g = Pin(39, Pin.OUT)
b = Pin(40, Pin.OUT)

  # 모두 끄기
r.off()
g.off()
b.off()

print("RGB LED 테스트 시작!")
print("-" * 50)

  # 1. 빨강만 켜기
print("1. 빨강 켜기...")
r.on()
input("Enter를 눌러 계속...")
r.off()

  # 2. 초록만 켜기
print("2. 초록 켜기...")
g.on()
input("Enter를 눌러 계속...")
g.off()

  # 3. 파랑만 켜기
print("3. 파랑 켜기...")
b.on()
input("Enter를 눌러 계속...")
b.off()

print("-" * 50)
print("테스트 완료!")