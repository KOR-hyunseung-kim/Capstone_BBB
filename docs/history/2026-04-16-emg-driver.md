# MyoWare 2.0 EMG 센서 드라이버 구현

**날짜**: 2026-04-16  
**작업자**: Claude (AI Assistant)  
**상태**: 완료

---

## 요약

MyoWare 2.0 EMG 센서가 도착하여, 신호 테스트 및 드라이버 구현을 완료했습니다.
ESP32-S3 DevKit에서 1kHz ADC 샘플링으로 근전도 신호를 수집하는 기본 구조를 구축했습니다.

---

## 주요 결정 사항

### 1. 하드웨어 배선
- **MyoWare 2.0 SIG** → **ESP32-S3 DevKit GPIO1** (ADC1_CH0)
- **MyoWare VS+** → **3.3V**
- **MyoWare GND** → **GND**

**주의**: ADC2(GPIO11~20)는 WiFi 활성화 시 사용 불가 → ADC1만 사용 가능

### 2. 개발 환경
- **IDE**: Thonny (MicroPython 개발 가장 간편)
- **플랫폼**: MicroPython (ESP32-S3 공식 포트)
- **테스트 방식**: 
  - 실시간 모니터링: `emg_quick_test.py` (Thonny REPL에서 직접 실행)
  - 단위 테스트: `pytest tests/test_emg.py` (PC에서 실행)

### 3. API 설계 (firmware/sensor/emg.py)
```python
emg = EMGSensor(adc_pin=1, sample_rate=1000)

# 단일 샘플
adc_val = emg.read_raw()      # 0~4095
mv_val = emg.read_mv()        # 0~3300 mV

# 연속 샘플링
samples = emg.sample_chunk(100)  # 100 샘플 @ 1kHz

# 스파이크 감지 (주먹 쥐기 감지용)
if emg.is_spike(threshold=3500):
    print("근수축 감지!")

# 자가 테스트
emg.test_sensor()  # 평균값 출력
```

### 4. 코딩 컨벤션
기존 `firmware/ui/motor.py`, `firmware/ui/led.py` 패턴 그대로 따름:
- Google style docstring (`Args:`, `Returns:`)
- 모든 public 메서드에 타입 힌트
- `test_*` 메서드로 자가 테스트 포함
- 줄 길이 88자 제한

---

## 구현 파일

### 1. `firmware/sensor/emg.py` — 메인 드라이버
```python
class EMGSensor:
    def __init__(adc_pin: int, sample_rate: int = 1000) → None
    def read_raw() → int                              # 0~4095
    def read_mv() → float                             # mV
    def sample_chunk(n_samples: int = 100) → list    # 연속 샘플
    def is_spike(threshold: int = 3500) → bool       # 스파이크 감지
    def test_sensor() → None                          # 자가 테스트
```

### 2. `firmware/sensor/emg_quick_test.py` — Thonny 실시간 테스트
- ESP32에 올려서 Thonny REPL에서 직접 실행
- 실시간으로 ADC 값, mV, 스파이크 감지 모니터링
- Ctrl+C로 중단

**사용법**:
1. XIAO를 USB로 PC에 연결
2. Thonny → "Tools" → "Options" → "Interpreter" → MicroPython 선택
3. `firmware/sensor/emg.py`를 ESP32 파일시스템에 저장
4. `emg_quick_test.py`를 Thonny에서 열어서 F5 실행
5. 출력 패널에서 실시간 값 확인

### 3. `tests/test_emg.py` — pytest 단위 테스트
- MockADC로 하드웨어 없이 테스트
- TestEMGSensor: ADC 변환 로직
- TestEMGSpikeDetection: 스파이크 임계값
- TestEMGSampleChunk: 샘플링 길이
- TestEMGNoiseFloor: 신호 품질

**실행**:
```bash
python -m pytest tests/test_emg.py -v
```

---

## 검증 절차

### PC 테스트 (하드웨어 없이)
```bash
cd C:\4_1\BBB
python -m pytest tests/test_emg.py -v
```
**예상 결과**: 모든 테스트 통과 ✓

### ESP32 실시간 테스트 (Thonny)
1. ESP32-S3 DevKit 연결
2. MyoWare 전극을 팔 근육에 부착
3. `emg_quick_test.py` 실행
4. 정지 상태: ADC ~600-1500 (정상)
5. 주먹 쥐기: ADC ~3500+ (스파이크 감지 ✓)

---

## 다음 단계

### 즉시 (필수)
1. ✓ Thonny 설치 및 MicroPython 플래싱 (사용자 진행)
2. ✓ MyoWare → ESP32 배선 완료 (사용자 진행)
3. ✓ `emg_quick_test.py` 로 신호 확인

### 후속 작업
- `firmware/sensor/imu.py` — MPU6050 드라이버 (Control Mode용)
- `tools/receiver.py` — WiFi UDP 수신 서버
- `firmware/algo/filter.py` — Band-pass 필터 (20~500Hz)
- Safety / Control 모드 전환 로직 통합

---

## 기술 노트

### ESP32-S3 ADC 설정
```python
adc = ADC(Pin(1))
adc.atten(ADC.ATTN_11DB)  # 0~3.3V 범위 (중요: MyoWare 아날로그 출력용)
adc.width(ADC.WIDTH_12BIT)  # 12-bit 해상도 (0~4095)
```

### 1kHz 샘플링 간격 계산
```python
sample_rate = 1000  # Hz
interval_us = 1_000_000 // sample_rate  # 1000 µs = 1 ms
time.sleep_us(interval_us)
```

### MyoWare 신호 범위 (일반적)
| 상태 | ADC 범위 | mV 범위 |
|------|---------|---------|
| 정지 (baseline) | 500~1500 | 400~1200 |
| 약한 수축 | 1500~2500 | 1200~2000 |
| 강한 수축 | 2500~4095 | 2000~3300 |

스파이크 임계값(3500) = 강한 수축 감지 기준점

### 디버깅 팁
- Thonny 터미널에서 `emg.test_sensor()` 호출 → 평균값으로 신호 품질 확인
- 정지 상태 ADC가 3000 이상이면 → 전극 위치 조정 (너무 강한 신호)
- ADC가 100 이하면 → 배선 확인 (신호 없음)

---

## 변경된 파일
- `firmware/sensor/emg.py` (신규)
- `firmware/sensor/emg_quick_test.py` (신규)
- `tests/test_emg.py` (신규)
- `docs/flow.md` (업데이트)

---

## 커밋 메시지
```
feat: implement MyoWare 2.0 EMG sensor driver

- Add EMGSensor class with 1kHz ADC sampling
- Support raw ADC reading and mV voltage conversion
- Implement spike detection for muscle contraction
- Add quick test script for Thonny REPL
- Include pytest unit tests (MockADC, conversion logic)
- Hardware: GPIO1 (ADC1_CH0) on ESP32-S3 DevKit
```


  🔧 ESP32에 프로그래밍하는 방법

  Step 1: Thonny IDE 설치

  # https://thonny.org 에서 Windows 설치 프로그램 다운로드
  # 또는
  pip install thonny

  Step 2: MicroPython 플래싱

  방법 A: Thonny 자동 플래싱 (권장)
  1. Thonny 실행
  2. 상단 메뉴 → "Tools" → "Options" → "Interpreter"
  3. "MicroPython (ESP32)" 선택
  4. 드롭다운에서 "Install or update MicroPython"
  5. "ESP32" 선택, 플래싱 시작 (자동)

  방법 B: 수동 플래싱 (esptool.py)
  pip install esptool

  # MicroPython 바이너리 다운로드
  # https://micropython.org/download/ESP32_GENERIC_S3/

  # 플래싱
  esptool.py --chip esp32s3 --port COM3 erase_flash
  esptool.py --chip esp32s3 --port COM3 write_flash -z 0x0
  ESP32_GENERIC_S3-*.bin

  Step 3: MyoWare 배선 (중요!)

  MyoWare 2.0       →    ESP32-S3 DevKit
  ─────────────────────────────────────
  SIG (신호)        →    GPIO1 (A0 핀, ADC1)
  VS+ (전원)        →    3.3V
  GND               →    GND

  ▎ ⚠️ 주의: ADC2(GPIO11~20)는 WiFi 활성화 시 사용 불가
  ▎ → 반드시 GPIO1 (ADC1) 사용하세요!

  Step 4: 드라이버 파일 ESP32에 복사

  1. Thonny를 열고 ESP32 연결
  2. firmware/sensor/emg.py 파일을 Thonny에서 오픈
  3. 상단 메뉴 → "File" → "Save as..." → "MicroPython device"
  4. emg.py로 저장

  Step 5: 신호 테스트

  1. firmware/sensor/emg_quick_test.py 파일을 Thonny에서 오픈
  2. F5 키 실행
  3. 하단 출력창에 실시간으로 ADC 값과 mV가 표시됨
  4. 팔에 전극 부착하고 주먹 쥐기 → 값이 올라가면 성공! ✓

  ---
  📊 API 레퍼런스

  from emg import EMGSensor

  # 초기화 (1kHz 샘플링)
  emg = EMGSensor(adc_pin=1, sample_rate=1000)

  # 단일 샘플 읽기
  adc_value = emg.read_raw()          # 0~4095
  voltage_mv = emg.read_mv()          # 0~3300 mV

  # 연속 100개 샘플 수집
  samples = emg.sample_chunk(100)     # @ 1kHz (100ms 소요)

  # 근수축(스파이크) 감지
  if emg.is_spike(threshold=3500):    # 기본값: 3500 ADC
      print("주먹 쥐기 감지!")         # Control Mode 클릭 트리거용

  # 자가 테스트 (신호 품질 확인)
  emg.test_sensor()
  # 출력: EMG test: avg=1200 (976mV), range=1050-1400
