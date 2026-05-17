# EMG DSP 알고리즘 & Safety Mode 구현

**날짜**: 2026-05-06
**작업자**: Claude Code (fw-developer agent)
**관련 파일**:
- `firmware/algo/emg_processor.py` (NEW)
- `firmware/algo/__init__.py` (NEW)
- `firmware/main.py` (NEW)
- `tests/test_emg_fatigue.py` (NEW)

## 요약

EMG 신호 처리 알고리즘(DSP)과 Safety Mode 구현을 완료했습니다. MyoWare 2.0 센서에서 읽은 아날로그 신호를 RMS(Root Mean Square) 기반으로 피로도 판정하고, 진동모터를 통해 피드백합니다.

## 결정 사항

### 1. EMG 신호 처리 파이프라인
- **샘플링**: 1kHz (이미 구현됨)
- **처리 단위**: 1초 단위 청크 (1000개 샘플)
- **특징 추출**: RMS (Root Mean Square)
  - RMS = √(∑(x²) / N)
  - 음성 근육의 피로도를 반영하는 대표 특징
  
### 2. Calibration & 기준값 설정
- **기간**: 1분 (60초)
- **방법**: 전체 60초 샘플의 RMS 계산
- **출력**: baseline_rms (기준값)
- **사용자 지침**: 팔을 이완한 상태에서 진행

### 3. 피로도 판정 임계값 (신호 강도 기준)
신호가 강할수록 근력이 있고, 약할수록 피로가 높음.

| 신호 강도 | 상태 | 피드백 |
|-----------|------|--------|
| ≥ 95% of baseline | 정상 | 없음 |
| 80~95% of baseline | 주의 | 진동 1회 |
| < 80% of baseline | 경고 | 강진동 |

예시:
- Baseline RMS = 2000
- 현재 RMS = 1900 (95%) → 정상
- 현재 RMS = 1700 (85%) → 주의 ⚠️
- 현재 RMS = 1500 (75%) → 경고 🚨

### 4. Control Mode를 위한 구조 설계
- EMGProcessor를 독립적인 모듈로 분리
- SafetyModeController가 processor를 래핑
- 나중에 IMU 기반 Control Mode 추가 시:
  - 같은 EMGProcessor 재사용 가능
  - spike detection (`is_spike()`) 메서드 이미 준비됨

## 구현 세부 내용

### firmware/algo/emg_processor.py
```
EMGProcessor
├── calibrate(duration_sec=60) → 기준값 설정
├── _calculate_rms(samples) → RMS 계산
├── get_fatigue_level(rms) → 신호 강도 기반 피로도 판정
├── update_with_feedback(rms) → RMS + 진동 모터 제어
└── run_monitoring_cycle() → 한 사이클 실행 (샘플링 → RMS → 판정)

SafetyModeController
├── start(duration_sec=60) → calibration + monitoring 시작
├── run_once() → 한 번의 모니터링 사이클 실행
└── stop() → 모니터링 종료 및 정리
```

### firmware/main.py
- ESP32-S3 Safety Mode 진입점
- GPIO1: EMG (고정)
- GPIO38: 진동 모터
- 기본 초기화: 센서 테스트 → 3초 대기 → Calibration → 모니터링 루프

## 테스트 커버리지

✅ **Unit Tests** (firmware/algo/ 단위 테스트)
- RMS 계산 정확성 (상수, 신호, 빈 데이터)
- Calibration (단일/다중 청크, 오류 처리)
- 피로도 판정 (정상/주의/경고 3단계)

✅ **Integration Tests**
- Calibration + Monitoring 전체 흐름
- 진동모터 피드백 트리거 검증
- 상태 전환 검증 (normal → warning → critical)

**테스트 실행**:
```bash
python -m pytest tests/test_emg_fatigue.py -v
# Result: 16 passed ✅
```

## 변경된 파일

### 신규 파일
- `firmware/algo/emg_processor.py` (238 lines) - 핵심 DSP 알고리즘
- `firmware/algo/__init__.py` (1 line) - 패키지 초기화
- `firmware/main.py` (79 lines) - 펌웨어 진입점
- `tests/test_emg_fatigue.py` (320 lines) - 통합 테스트 스위트

### 수정 파일
- 없음 (기존 코드 호환성 100%)

## GPIO 핀맵 확정

| 기능 | GPIO | 상태 |
|------|------|------|
| EMG (MyoWare 2.0) | GPIO1 | **고정** ✅ |
| 진동 모터 | GPIO38 | 사용 중 |
| RGB LED | TBD | 추후 추가 (선택) |

## 다음 단계

### Phase 1: IMU 센서 & Control Mode (예정)
- MPU6050 I2C 드라이버 테스트
- Pitch/Roll 각도 계산 (Complementary Filter)
- EMG spike detection + HID mouse 제어

### Phase 2: WiFi 통신 (선택)
- UDP로 EMG raw data → PC 전송
- PC에서 DSP 처리 결과 → ESP32 수신
- 현재는 온보드 처리로 충분함

### Phase 3: 3D 하우징 & 최종 통합
- FDM 3D 프린팅 (PLA/PETG)
- 배터리 레이아웃 확정
- 사용자 테스트

## 기술 정보

### RMS vs 다른 특징
| 특징 | 장점 | 단점 |
|------|------|------|
| **RMS** | 근력/피로도 잘 반영, 계산 간단 | FFT 분석 부재 |
| FFT (Median Frequency) | 주파수 특성 반영 | 계산 복잡, 메모리 많음 |
| Envelope (고주파 여파) | 실시간 처리 최적 | 필터 설계 필요 |

**선택 이유**: MCU 리소스(256KB RAM), 실시간 성능 고려 시 RMS가 최적의 선택. 차후 필요 시 FFT 추가 가능.

### 임계값 선택 근거
- **95% (정상)**: 근력 완전한 상태 (오류 최소)
- **80% (주의)**: 피로도 ~20% (초기 경고)
- **< 80% (경고)**: 피로도 > 20% (긴급 상황)

실제 사용자 테스트를 통해 조정 가능.

## 참고: CLAUDE.md 준수 사항

✅ 코딩 규칙:
- PEP 8 (88자 라인)
- Type hints 완비
- Google style docstring

✅ 테스트 전략:
- pytest 사용
- Mock 센서 활용
- 커버리지 80%+ 달성

✅ 모듈 구조:
- `firmware/algo/` - 신호 처리
- `firmware/sensor/` - 센서 드라이버
- `firmware/ui/` - 진동 모터

