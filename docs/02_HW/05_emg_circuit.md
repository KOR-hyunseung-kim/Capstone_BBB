# EMG 센서 회로 (MyoWare 2.0)

**목적**: 근전도 신호 수집 (1kHz 샘플링, 아날로그 → 디지털 변환)

---

## 부품 목록

| 부품 | 모델 | 수량 | 비고 |
|------|------|------|------|
| EMG 센서 | MyoWare 2.0 Basic Kit (DEV-21267) | 1 | 신호 처리 기판 + 전극 포함 |
| 전극 | 일회용 생의료용 전극 | 3 | 센서 키트에 포함 |
| GPIO | GPIO1 | 1 | ADC1_CH0 (WiFi 안전) |

---

## MyoWare 2.0 센서 구조

```
┌─────────────────────────────────┐
│   MyoWare 2.0 센서 모듈         │
│  (신호처리 + 증폭 회로)         │
│                                 │
│  [전극부] ──→ [증폭기] ──→      │
│  (팔 표면)    (40~1000V/V)     │
│                        ↓        │
│                   [아날로그 출력]│
│                        (0~3.3V) │
└─────────────────────────────────┘
         ↓
      3핀 JST 커넥터
      ├─ SIG (신호)
      ├─ VS+ (3.3V 전원)
      └─ GND (그라운드)
```

---

## 회로도

```
        ┌──────────────────┐
        │  MyoWare 2.0     │
        │  센서 모듈       │
        └────────┬─────────┘
          3핀 커넥터
          │
          ├─ SIG ──────────→ GPIO1 (ADC1_CH0)
          ├─ VS+ ──────────→ 3.3V
          └─ GND ──────────→ GND

배선도:
MyoWare (SIG) ──────── ESP32 GPIO1
MyoWare (VS+) ──────── ESP32 3.3V
MyoWare (GND) ──────── ESP32 GND
```

---

## 전극 부착 위치

```
팔 위치:
┌─────────────────────────────┐
│     팔 (상완근)              │
│  ┌───────────────────────┐  │
│  │  전극 부착 영역        │  │
│  │  (상완 이두근 중앙)   │  │
│  │                       │  │
│  │  정상 EMG 신호:      │  │
│  │  600~1500 mV (정지)  │  │
│  │  1500~3000 mV (약함) │  │
│  │  3000+ mV (강함)     │  │
│  └───────────────────────┘  │
└─────────────────────────────┘

전극 배치:
신호 전극 ├─┤ 기준 전극 (간격 2~3cm)
        (둘 다 근육 위)
        
        그라운드 전극 (뼈 또는 중립 부위)
```

---

## ADC 설정 (MicroPython)

### 초기화

```python
from machine import ADC, Pin

# GPIO1을 ADC로 설정
adc = ADC(Pin(1))

# 기본 설정 (ESP32-S3)
adc.atten(ADC.ATTN_11DB)   # 0~3.3V 범위 (중요!)
adc.width(ADC.WIDTH_12BIT) # 12-bit 해상도 (0~4095)

# 확인
print(f"ADC 범위: {adc.read()}") # 0~4095 값 출력
```

### 단일 샘플 읽기

```python
# 아날로그 → 디지털 변환
raw_adc = adc.read()  # 0~4095

# ADC → 전압(mV) 변환
voltage_mv = raw_adc * 3300 // 4095

print(f"ADC: {raw_adc}, Voltage: {voltage_mv}mV")
```

### 1kHz 샘플링 (연속 수집)

```python
import time

sample_rate = 1000  # Hz
sample_period_us = 1_000_000 // sample_rate  # 1000 µs = 1 ms

def sample_emg(n_samples=1000):
    """n_samples 개를 1kHz로 샘플링"""
    samples = []
    for _ in range(n_samples):
        samples.append(adc.read())
        time.sleep_us(sample_period_us)
    return samples

# 실행
data = sample_emg(100)  # 100 샘플 = 100ms
print(f"수집: {len(data)} 샘플, 평균: {sum(data)//len(data)}")
```

---

## 신호 범위 (일반적인 MyoWare)

| 상태 | ADC 범위 | mV 범위 | 의미 |
|------|---------|---------|------|
| 정지 (baseline) | 500~1500 | 400~1200 | 센서 정상 |
| 약한 수축 | 1500~2500 | 1200~2000 | 가벼운 움직임 |
| 강한 수축 | 2500~4095 | 2000~3300 | 주먹 쥐기 (임계값 ~3500) |

---

## 테스트 코드 (Thonny REPL)

### 1단계: 기본 연결 확인

```python
from machine import ADC, Pin
import time

adc = ADC(Pin(1))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

# 1초 동안 10번 읽기
for i in range(10):
    print(f"ADC: {adc.read()}")
    time.sleep(0.1)
```

**예상 출력**: 600~2000 범위의 안정적인 값

### 2단계: 정지 상태 평균값

```python
# 정지 상태에서 100 샘플 평균
samples = [adc.read() for _ in range(100)]
avg = sum(samples) // len(samples)
print(f"평균: {avg}, 범위: {min(samples)}~{max(samples)}")
```

**예상**: 평균 ~1000, 범위 500~1500

### 3단계: 주먹 쥐기 테스트

```python
print("정지 상태...")
time.sleep(1)
base = adc.read()
print(f"Baseline: {base}")

print("주먹 쥐기!")
max_val = max([adc.read() for _ in range(100)])
print(f"Max: {max_val}")
```

**예상**: max_val이 baseline보다 1000 이상 높음

---

## 펌웨어 코드 (EMGSensor 클래스)

```python
# firmware/sensor/emg.py

from machine import ADC, Pin
import time

class EMGSensor:
    """MyoWare 2.0 EMG 센서 드라이버"""
    
    def __init__(self, adc_pin: int = 1, sample_rate: int = 1000):
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        self.sample_rate = sample_rate
        self.sample_period_us = 1_000_000 // sample_rate
    
    def read_raw(self) -> int:
        """0~4095 ADC 값 읽기"""
        return self.adc.read()
    
    def read_mv(self) -> float:
        """0~3300 mV 전압 읽기"""
        raw = self.read_raw()
        return raw * 3300 / 4095
    
    def sample_chunk(self, n_samples: int = 100) -> list:
        """n_samples개를 1kHz로 샘플링"""
        samples = []
        for _ in range(n_samples):
            samples.append(self.read_raw())
            time.sleep_us(self.sample_period_us)
        return samples
    
    def is_spike(self, threshold: int = 3500) -> bool:
        """주먹 쥐기 감지 (임계값 초과?)"""
        return self.read_raw() > threshold
    
    def test_sensor(self) -> None:
        """자가 테스트 (신호 품질 확인)"""
        samples = self.sample_chunk(100)
        avg = sum(samples) // len(samples)
        min_val = min(samples)
        max_val = max(samples)
        print(f"EMG test: avg={avg} ({avg*3300//4095}mV), range={min_val}-{max_val}")

# 사용 예
emg = EMGSensor(adc_pin=1)
print(emg.read_raw())    # 단일 샘플
data = emg.sample_chunk(100)  # 100 샘플 수집
emg.test_sensor()        # 자가 테스트
```

---

## 배선 체크리스트

```
[ ] MyoWare SIG → GPIO1 (ADC1_CH0)
[ ] MyoWare VS+ → 3.3V
[ ] MyoWare GND → GND
[ ] 전극 팔에 부착 (간격 2~3cm)
[ ] 정지 상태 ADC 확인 (500~1500 범위)
[ ] 주먹 쥐기 ADC 확인 (3000+ 범위)
```

---

## 주의사항

**중요**: ADC2(GPIO11~20) 사용 금지!
```
이유: WiFi 활성화 시 ADC2 공유 → 신호 노이즈 증가
해결: GPIO1 (ADC1) 반드시 사용
```

---

## 관련 파일

- `docs/02_HW/01_overall_circuit.md` — 전체 회로도
- `firmware/sensor/emg.py` — EMG 드라이버
- `firmware/sensor/emg_quick_test.py` — Thonny 테스트 스크립트
- `tests/test_emg.py` — pytest 단위 테스트
