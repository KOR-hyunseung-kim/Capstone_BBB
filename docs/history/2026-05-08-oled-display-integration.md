# OLED 디스플레이 통합 및 안정화

**날짜**: 2026-05-08
**작업자**: Claude Code (fw-developer agent)
**관련 파일**:
- `firmware/config.py` (I2C 속도 조정)
- `firmware/ui/oled.py` (드라이버 재작성, 기능 확장)
- `firmware/algo/emg_processor.py` (Calibration OLED 피드백)
- `tests/test_oled_simple.py` (NEW: 진단 테스트)
- `tests/test_i2c_scan.py` (NEW: I2C 스캔 진단)

## 요약

OLED(SSD1306 128x64, 단일 색상 White) 디스플레이를 완전 통합했습니다.
- I2C 통신 안정화
- 깔끔한 UI 레이아웃 (센터 정렬)
- Calibration 중 진행률 표시
- 실시간 EMG % + 상태 표시

## 주요 변경 사항

### 1. 핀맵 명확화 (`firmware/config.py`)

```python
# OLED Pin Mapping: VDD(3.3V) → VCC, GND → GND, SCK → GPIO9, SDA → GPIO8
I2C_SDA_PIN = 8   # GPIO8 - I2C SDA (OLED SDA pin)
I2C_SCL_PIN = 9   # GPIO9 - I2C SCL / SCK (OLED SCK pin)
I2C_FREQUENCY = 100_000  # 낮춰서 안정성 증가 (400kHz → 100kHz)
```

**이유**: 
- OLED 모델명 MN09612864-4G / PN-OLED-W096 SSD1306 확인
- 원래는 400kHz였지만 I2C 버스 안정성을 위해 100kHz로 조정

### 2. ssd1306 드라이버 내장 (`firmware/ui/oled.py`)

기존: 외부 라이브러리 import 시도 → 실패 → mock display
현재: ssd1306 전체 코드를 oled.py에 내장

```python
# 임베디드 SSD1306 클래스 추가
class SSD1306:
    def init_display(self):
        # 공식 SSD1306 초기화 시퀀스
        # 각 명령어 사이 1ms 대기로 안정성 향상
        
    def write_data(self, buf):
        # I2C 데이터를 16바이트 청크로 나눠 전송
        # 한 번에 너무 큰 데이터 전송 방지
```

**개선 사항**:
- ✅ 별도 파일 업로드 불필요
- ✅ I2C 통신 안정화 (청크 단위 전송)
- ✅ 명령어 간 타이밍 추가

### 3. UI 메서드 확장 (`firmware/ui/oled.py`)

#### `draw()` - 실시간 모니터링 화면
```
┌──────────────────────┐
│  BBB Safety Mode     │
│     85.5%            │  ← 큰 글자, 센터
│  [████████    ]      │  ← 프로그레스 바
│     OK               │  ← 상태 텍스트
│  MF: 150Hz           │  ← Median Frequency
└──────────────────────┘
```

#### `show_message(text1, text2, text3)` - 안내 메시지
```
Calibrating...
Please RELAX
your arm
```

#### `show_progress(title, percent)` - 진행률 표시
```
Calibrating
85%
[██████████  ]
```

### 4. Calibration 중 OLED 피드백 추가

**emg_processor.py 변경:**
```python
def calibrate(self, duration_sec=60, oled_display=None):
    # Calibration 시작 전
    oled_display.show_message("Calibrating...", "Please RELAX", "your arm")
    
    # Calibration 진행 중 (매초)
    for i in range(n_chunks):
        progress = int((i + 1) * 100 / n_chunks)
        oled_display.show_progress("Calibrating", progress)
    
    # 완료 후
    oled_display.show_message("Calibration", "Complete!", f"BL:{baseline_rms:.0f}")
```

**SafetyModeController.start() 변경:**
```python
if not self.processor.calibrate(duration_sec, oled_display=self.oled):
    # ↑ OLED 파라미터 전달
```

### 5. 진단 도구 추가

#### `tests/test_i2c_scan.py`
- I2C 디바이스 스캔
- OLED(0x3c) 인식 확인

#### `tests/test_oled_simple.py`
- OLED 초기화 및 표시 테스트
- 여러 상태(normal/warning/critical) 테스트
- 문제 발생 지점 파악

**테스트 결과**: ✅ 테스트 코드에서는 OLED 정상 작동 확인

### 6. 색상 표시 제거

단일 색상 흑백 OLED이므로:
- RGB LED와 별도로 관리
- OLED: 텍스트 기반 상태 표시 (OK / WARNING / CRITICAL!)
- LED: RGB 색상 표시 (별도)

## 기술 스펙

| 항목 | 값 |
|------|-----|
| **OLED 모델** | PN-OLED-W096 SSD1306 |
| **해상도** | 128x64 픽셀 |
| **색상** | 단일 색상 (White) |
| **I2C 주소** | 0x3C |
| **I2C 속도** | 100 kHz |
| **통신 방식** | I2C (GPIO8 SDA, GPIO9 SCL) |

## GPIO 최종 확인

| 기능 | GPIO | I2C Addr | 상태 |
|------|------|----------|------|
| EMG ADC | GPIO1 | - | ✅ |
| 진동모터 | GPIO38 | - | ✅ |
| RGB LED R | GPIO17 | - | ✅ |
| RGB LED G | GPIO18 | - | ✅ |
| RGB LED B | GPIO19 | - | ✅ |
| I2C SDA | GPIO8 | 0x3C (OLED) | ✅ |
| I2C SCL | GPIO9 | 0x68 (IMU) | ✅ |

## 테스트 결과

### ✅ Passed
- I2C 스캔: OLED(0x3c) 인식 ✓
- OLED 초기화: 성공 ✓
- draw() 함수: 실시간 표시 ✓
- show_message(): 메시지 표시 ✓
- show_progress(): 진행률 표시 ✓
- 데이터 전송 안정성: 청크 단위 ✓

### 해결된 문제
1. **글자 짤림** → START LINE 레지스터 명시적 설정
2. **화면 노이즈** → I2C 데이터 청크 단위 전송
3. **라이브러리 미발견** → 드라이버 내장
4. **초기화 불안정** → 공식 SSD1306 시퀀스 + 타이밍 추가

## 현재 OLED 표시 흐름

```
[Init] 부팅
  ↓
[OLED] I2C 초기화
  ↓
[Calib] "Calibrating..." 메시지 + 진행률 바 (0-100%)
  ↓
[Monitor] 실시간 % + 상태 표시
  ├─ "OK" (정상 ≥90%)
  ├─ "WARNING" (주의 70-90%)
  └─ "CRITICAL!" (경고 <70%, 깜빡임)
```

## 다음 단계

1. **실제 하드웨어 테스트** (납땜 완료 후)
   - 센서 신호 확인
   - Calibration 진행률 OLED 표시 검증
   - 실시간 모니터링 정확성 확인

2. **Control Mode 준비**
   - IMU(MPU6050) 드라이버 구현
   - BLE HID 마우스 구현

3. **3D 하우징 설계**
   - OLED 베젤
   - 배터리 고정

## 파일 구조 최종

```
firmware/
├── config.py                          ← I2C 속도 100kHz
├── ui/
│   └── oled.py                        ← SSD1306 드라이버 내장
│       ├── class SSD1306
│       └── class OLEDDisplay
└── algo/
    └── emg_processor.py               ← calibrate(oled_display=)
        ├── calibrate() - OLED 피드백
        └── SafetyModeController.start()

tests/
├── test_i2c_scan.py                   ← NEW: I2C 진단
└── test_oled_simple.py                ← NEW: OLED 진단
```

## 배포 체크리스트

- [x] I2C 핀맵 명확화 (config.py)
- [x] ssd1306 드라이버 내장 (oled.py)
- [x] OLED UI 메서드 확장 (show_message, show_progress)
- [x] Calibration OLED 피드백 (emg_processor.py)
- [x] I2C 안정성 개선 (청크 단위 전송)
- [x] 진단 테스트 도구 작성
- [ ] 실제 하드웨어 통합 테스트 (납땜 후)
- [ ] EMG 신호 정확성 검증
- [ ] LED + OLED + Motor 동시 작동 확인

## 커밋 메시지

```
feat: OLED 디스플레이 완전 통합 및 안정화

- SSD1306 드라이버 내장 (외부 라이브러리 불필요)
- I2C 속도 100kHz로 조정 (안정성 향상)
- OLED 초기화 시퀀스 강화 (명령어 간 타이밍)
- I2C 데이터 청크 단위 전송 (16바이트)
- show_message(), show_progress() 메서드 추가
- Calibration 중 진행률 표시
- 진단 도구: test_i2c_scan.py, test_oled_simple.py
- 색상 표시 제거 (단일 색상 흑백 대응)
```
