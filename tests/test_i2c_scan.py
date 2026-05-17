"""
I2C Device Scanner - OLED 연결 진단
ESP32에서 실행: Thonny 또는 webrepl로 이 코드를 복사&붙여넣기
"""

from machine import I2C, Pin

# GPIO 설정 (config.py와 동일)
I2C_SDA_PIN = 8
I2C_SCL_PIN = 9
I2C_FREQUENCY = 400_000

print("=" * 50)
print("I2C Device Scanner")
print("=" * 50)

try:
    # I2C 초기화
    print(f"\n[Init] I2C 초기화...")
    print(f"  SDA: GPIO{I2C_SDA_PIN}")
    print(f"  SCL: GPIO{I2C_SCL_PIN}")
    print(f"  Frequency: {I2C_FREQUENCY} Hz")

    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQUENCY)
    print("✓ I2C 초기화 성공")

    # I2C 스캔
    print("\n[Scan] 연결된 I2C 디바이스 검색...")
    devices = i2c.scan()

    if devices:
        print(f"\n✓ {len(devices)}개의 디바이스 발견:")
        for addr in devices:
            addr_hex = hex(addr)
            print(f"  - I2C Address: {addr_hex} (decimal: {addr})")

            # OLED 주소 확인
            if addr == 0x3C:
                print(f"    → ✓ SSD1306 OLED 인식됨!")
            elif addr == 0x68:
                print(f"    → ✓ MPU6050 IMU 인식됨!")
    else:
        print("\n✗ I2C 디바이스를 찾을 수 없습니다!")
        print("\n[확인 사항]")
        print("  1. VDD(전원) → 3.3V 연결 확인")
        print("  2. GND(그라운드) → GND 연결 확인")
        print("  3. SDA → GPIO8 연결 확인")
        print("  4. SCK(SCL) → GPIO9 연결 확인")
        print("  5. 풀업 저항(4.7k Ohm) 추가 필요할 수 있음")

except Exception as e:
    print(f"\n✗ I2C 초기화 실패: {e}")
    print("\n[해결 방법]")
    print("  - GPIO 번호 재확인")
    print("  - OLED 연결선 재확인")
    print("  - ESP32 재부팅")

print("\n" + "=" * 50)
