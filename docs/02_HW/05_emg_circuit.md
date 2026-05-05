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

## MyoWare 2.0 센서 구조 (고급 모듈)

```
┌─────────────────────────────────┐
│   MyoWare 2.0 센서 모듈         │
│  (신호처리 + 증폭 회로)         │
│                                 │
│  [전극부]                       │
│  (팔 표면)                      │
│     ↓                           │
│  [증폭기 40~1000V/V]            │
│     ↓                           │
│  [고주파 필터 150Hz]            │
│     ├─→ RAW (원본)              │
│     │                           │
│     └─→ [전파 정류]             │
│         ├─→ RECT (정류)         │
│         │                       │
│         └─→ [저주파 필터]       │
│             └─→ ENV (포괄신호)  │
│                 (권장 사용!)     │
└─────────────────────────────────┘
         ↓
    핀 구성:
    ├─ GND (그라운드)
    ├─ 3V3 (3.3V 전원)
    ├─ ENV (포괄 신호) ← 추천!
    ├─ RECT (정류 신호)
    └─ RAW (원본 신호)
```

---

## 세 가지 출력 신호 비교

| 신호 | 설명 | 범위 | 용도 | 샘플링 |
|------|------|------|------|--------|
| **RAW** | 원본 EMG 신호 (필터링 X) | 0~3.3V (진동 O) | FFT 분석, 고주파 포함 필요시 | 1kHz+ |
| **RECT** | 전파 정류 (절댓값) | 0~3.3V (직류화) | 실시간 강도 감지 | 100Hz+ |
| **ENV** | 포괄 신호 (저주파만) | 0~3.3V (부드러움) | **피로도 판정 (권장)** | 50Hz+ |

**BBB 프로젝트**: **ENV 신호 사용** ✓
- 이미 필터링됨 (고주파 제거)
- 피로도 판정에 필요한 저주파만 포함
- ADC 샘플링 부담 적음

---

## 회로도 (ENV 신호 사용)

```
        ┌──────────────────┐
        │  MyoWare 2.0     │
        │  센서 모듈       │
        └────────┬─────────┘
          5핀 헤더
          │
          ├─ GND ──────────→ ESP32 GND
          ├─ 3V3 ──────────→ ESP32 3.3V
          ├─ ENV ──────────→ GPIO1 (ADC1_CH0) ← 추천
          ├─ RECT ────────→ (미사용)
          └─ RAW ─────────→ (미사용)

배선도:
MyoWare (GND) ────────── ESP32 GND
MyoWare (3V3) ────────── ESP32 3.3V
MyoWare (ENV) ────────── ESP32 GPIO1 (ADC1_CH0)
MyoWare (RECT, RAW) ──── (연결 안 함)
```

---

## 신호별 사용 예시

### ENV 신호 (추천 - BBB용)

```
정지: 0.5~1.0V (안정적)
약한 근육 수축: 1.0~2.0V
강한 근육 수축: 2.0~3.0V+

특징:
- 이미 필터링됨 (250Hz 이상 제거)
- 저주파 성분 강조
- 부드러운 곡선 → FFT 분석 용이
```

### RAW 신호 (고급 분석용)

```
정지: 0.5~1.5V (높은 주파수 잡음 있음)
근육 수축: 진동하는 파형 (500Hz~1kHz)

특징:
- 원본 신호 (필터링 X)
- 고주파 잡음 많음
- FFT로 주파수 분석 가능
- 고속 샘플링 필요 (5kHz+)
```

### RECT 신호 (실시간 강도 감지)

```
정지: 0.3~0.8V (평탄)
근육 수축: 2.0~3.0V (높음)

특징:
- 절댓값 처리 (음수 없음)
- 직류화 → 빠른 반응
- 주파수 정보 손실
- 간단한 임계값 비교 가능
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

## 신호 범위 (ENV 포트, MyoWare 2.0)

| 상태 | ADC 범위 | mV 범위 | 의미 |
|------|---------|---------|------|
| 정지 (baseline) | 150~350 | 120~280 | 센서 정상 |
| 약한 수축 | 350~800 | 280~650 | 가벼운 움직임 |
| 중간 수축 | 800~2000 | 650~1600 | 일반적인 움직임 |
| 강한 수축 | 2000~3500 | 1600~2800 | 주먹 쥐기 강하게 |
| 매우 강한 수축 | 3500~4095 | 2800~3300 | 극한 근력 (피로도 95%+) |

**참고**: ENV 신호는 이미 필터링되어 RAW 신호보다 값이 낮고 변화가 부드럽습니다.

---

## 테스트 코드 (Thonny REPL) - ENV 신호용

### 1단계: 기본 연결 확인

```python
from machine import ADC, Pin
import time

# GPIO1 (ENV 신호) ADC 초기화
adc = ADC(Pin(1))
adc.atten(ADC.ATTN_11DB)    # 0~3.3V 범위
adc.width(ADC.WIDTH_12BIT)  # 12-bit (0~4095)

# 1초 동안 10번 읽기
print("ENV 신호 읽기:")
for i in range(10):
    raw = adc.read()
    mv = raw * 3300 // 4095
    print(f"ADC: {raw:4d} | Voltage: {mv:4d}mV")
    time.sleep(0.1)
```

**예상 출력** (정지 상태): 150~350 범위의 안정적인 값

### 2단계: 정지 상태 평균값 (기준값 설정)

```python
# 정지 상태에서 100 샘플 수집 → 기준값 설정
print("정지 상태, 100 샘플 평균...")
samples = [adc.read() for _ in range(100)]
baseline = sum(samples) // len(samples)
min_s = min(samples)
max_s = max(samples)

print(f"기준값: {baseline} ADC ({baseline*3300//4095}mV)")
print(f"범위: {min_s}~{max_s}")
```

**예상**: 
- 평균 ~250 ADC
- 범위 150~350 ADC
- mV 범위: 120~280mV

### 3단계: 주먹 쥐기 테스트

```python
import time

print("정지 상태 기준값 설정...")
baseline = sum([adc.read() for _ in range(100)]) // 100
print(f"Baseline: {baseline} ADC")
time.sleep(1)

print("이제 천천히 주먹을 쥐세요...")
time.sleep(2)

print("주먹 쥐기 신호 기록 (5초):")
print("-" * 50)
max_val = 0
for i in range(50):  # 5초 = 50 × 100ms
    raw = adc.read()
    mv = raw * 3300 // 4095
    increase = raw - baseline
    marker = "👊" if raw > baseline + 500 else "  "
    
    print(f"ADC: {raw:4d} ({increase:+4d}) | mV: {mv:4d} {marker}")
    max_val = max(max_val, raw)
    time.sleep(0.1)

print("-" * 50)
print(f"최대값: {max_val} ADC ({max_val - baseline:+d})")
```

**예상 패턴**:
```
정지: ADC 200~300
주먹 쥐기: ADC 2500~3500+ (기준값보다 2000+ 높음)
다시 정지: ADC 200~300
```

---

## 펌웨어 코드 (EMGSensor 클래스 - ENV 신호용)

```python
# firmware/sensor/emg.py

from machine import ADC, Pin
import time

class EMGSensor:
    """MyoWare 2.0 EMG 센서 드라이버 (ENV 포트)"""
    
    def __init__(self, adc_pin: int = 1, sample_rate: int = 100):
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)  # 0~3.3V
        self.adc.width(ADC.WIDTH_12BIT)  # 12-bit (0~4095)
        self.sample_rate = sample_rate
        self.sample_period_us = 1_000_000 // sample_rate
        
        # 캘리브레이션 (정지 상태 평균값)
        self.baseline = self._calibrate()
    
    def _calibrate(self) -> int:
        """정지 상태에서 기준값 설정 (100 샘플)"""
        samples = [self.read_raw() for _ in range(100)]
        return sum(samples) // len(samples)
    
    def read_raw(self) -> int:
        """0~4095 ADC 값 읽기 (ENV 신호)"""
        return self.adc.read()
    
    def read_mv(self) -> float:
        """0~3300 mV 전압 읽기"""
        raw = self.read_raw()
        return raw * 3300 / 4095
    
    def read_relative(self) -> int:
        """기준값 대비 상대값 (피로도 판정용)"""
        return self.read_raw() - self.baseline
    
    def sample_chunk(self, n_samples: int = 100) -> list:
        """n_samples개를 설정된 샘플링 레이트로 수집"""
        samples = []
        for _ in range(n_samples):
            samples.append(self.read_raw())
            time.sleep_us(self.sample_period_us)
        return samples
    
    def is_spike(self, threshold: int = 800) -> bool:
        """주먹 쥐기 감지 (기준값 대비 임계값)
        
        기본값 800 = 기준값보다 약 800 높음
        - 약한 수축: 200~400
        - 일반적인 움직임: 400~800
        - 강한 수축: 800~2000
        - 매우 강함: 2000+
        """
        return self.read_relative() > threshold
    
    def test_sensor(self) -> None:
        """자가 테스트 (신호 품질 확인)"""
        samples = self.sample_chunk(100)
        avg = sum(samples) // len(samples)
        min_val = min(samples)
        max_val = max(samples)
        avg_mv = avg * 3300 // 4095
        print(f"EMG test: baseline={self.baseline}, avg={avg} ({avg_mv}mV), range={min_val}-{max_val}")

# 사용 예
emg = EMGSensor(adc_pin=1, sample_rate=100)  # ENV는 50Hz 샘플링으로 충분
print(emg.read_raw())                # 단일 샘플
print(emg.read_relative())           # 기준값 대비 상대값
data = emg.sample_chunk(100)         # 100 샘플 수집
emg.test_sensor()                    # 자가 테스트

# 피로도 감지
if emg.is_spike(threshold=800):
    print("주먹 쥐기 감지!")
```

---

## 배선 체크리스트 (ENV 신호용)

```
[ ] MyoWare GND → ESP32 GND
[ ] MyoWare 3V3 → ESP32 3.3V
[ ] MyoWare ENV → GPIO1 (ADC1_CH0) ← **핵심: ENV 사용!**
[ ] MyoWare RECT → (연결 안 함, 선택적)
[ ] MyoWare RAW → (연결 안 함, 선택적)
[ ] 전극 팔에 부착 (간격 2~3cm)
[ ] 정지 상태 ADC 확인 (150~350 범위)
[ ] 주먹 쥐기 ADC 확인 (2500+ 범위)
```

## MyoWare 포트별 사용 정리

| 포트 | 용도 | BBB 프로젝트 | 비고 |
|------|------|-------------|------|
| **GND** | 그라운드 | ✓ 필수 | 전원 기준 |
| **3V3** | 3.3V 전원 | ✓ 필수 | 센서 전원 |
| **ENV** | 포괄 신호 (저주파) | ✓ **추천** | 필터링됨, 피로도 판정 최적 |
| **RECT** | 정류 신호 | △ 선택 | 실시간 강도 감지용 |
| **RAW** | 원본 신호 (고주파) | △ 선택 | FFT 분석용 (고속 샘플링 필요) |

**BBB에서는 ENV만 사용!**

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
