"""
OLED 간단한 테스트 - 초기화 및 기본 표시만 확인
Thonny/WebREPL에서 실행
"""

from machine import I2C, Pin
import time

print("=" * 50)
print("OLED 간단한 테스트")
print("=" * 50)

# I2C 초기화
print("\n[1] I2C 초기화 중...")
try:
    i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100_000)
    print("✓ I2C 초기화 성공")
except Exception as e:
    print(f"✗ I2C 초기화 실패: {e}")
    exit()

# 디바이스 스캔
print("\n[2] I2C 디바이스 검색...")
devices = i2c.scan()
if 0x3c in devices:
    print("✓ OLED(0x3c) 발견")
else:
    print("✗ OLED를 찾을 수 없습니다")
    exit()

# OLED 초기화 및 표시
print("\n[3] OLED 표시 테스트...")
try:
    # ui 폴더의 oled 모듈 import
    import sys
    sys.path.insert(0, '/firmware')
    from ui.oled import OLEDDisplay

    oled = OLEDDisplay(i2c, 128, 64, 0x3c)
    print("✓ OLEDDisplay 객체 생성 완료")

    # 테스트: 여러 값으로 업데이트
    test_values = [
        {"fatigue_pct": 45.0, "mf": 120.5, "level": "normal"},
        {"fatigue_pct": 75.0, "mf": 110.0, "level": "warning"},
        {"fatigue_pct": 25.0, "mf": 95.5, "level": "critical"},
    ]

    for i, data in enumerate(test_values):
        print(f"\n[{i+1}] 업데이트 중: {data}")
        try:
            oled.update(data)
            print(f"   ✓ {data['fatigue_pct']:.1f}% / {data['level']}")
            time.sleep(2)
        except Exception as e:
            print(f"   ✗ 업데이트 실패: {e}")

    oled.clear()
    print("\n✓ 테스트 완료!")

except Exception as e:
    print(f"✗ OLED 표시 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
