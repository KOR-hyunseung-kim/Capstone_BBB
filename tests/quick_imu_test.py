from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(15), sda=Pin(16), freq=400000)

# 완전한 초기화
i2c.writeto(0x68, bytes([0x6B, 0x80]))  # 리셋
time.sleep(1)

i2c.writeto(0x68, bytes([0x6B, 0x00]))  # 파워 온
time.sleep(0.2)

i2c.writeto(0x68, bytes([0x1A, 0x06]))  # DLPF 5Hz (필터)
i2c.writeto(0x68, bytes([0x1B, 0x00]))  # 자이로
i2c.writeto(0x68, bytes([0x1C, 0x00]))  # 가속도
time.sleep(0.2)

print("안정적인 데이터 읽기 테스트")
print("-" * 50)

for i in range(20):
    data = i2c.readfrom(0x68, 14)

    ax = ((data[0] << 8) | data[1])
    ay = ((data[2] << 8) | data[3])
    az = ((data[4] << 8) | data[5])

    if ax & 0x8000: ax -= 0x10000
    if ay & 0x8000: ay -= 0x10000
    if az & 0x8000: az -= 0x10000

    print(f"AX:{ax:7d} AY:{ay:7d} AZ:{az:7d}")
    time.sleep(0.2)
