# BBB 관리자 모니터링 시스템 설계 및 구현

**날짜**: 2026-04-12  
**작업자**: Claude Code  
**관련 파일**:
- `tools/dashboard/server.py` — FastAPI + WebSocket 서버
- `tools/dashboard/static/` — 웹 대시보드 UI
- `firmware/ui/oled.py` — OLED 디스플레이 드라이버
- `firmware/ui/led.py` — RGB LED 제어기
- `firmware/ui/motor.py` — 진동모터 제어기
- `firmware/comm/wifi.py` — UDP 양방향 통신
- `requirements.txt` — 의존성 추가
- `tests/test_dashboard.py`, `tests/test_oled.py` — 단위 테스트

---

## 요약

원격 관리자가 실시간으로 근무자의 피로도를 모니터링하고, 근무자도 장치에 장착된 OLED와 LED·진동피드백으로 즉시 피드백을 받을 수 있는 **이중 피드백 구조**를 설계 및 구현함.

### 시스템 아키텍처

```
[ESP32-S3 센서] 
    ↓ WiFi UDP (EMG/IMU raw)
[PC DSP 서버]
    ├→ UDP 역전송 (분석 결과)
    │     ↓
    ├→ [ESP32 출력]
    │     ├─ OLED 디스플레이
    │     ├─ RGB LED
    │     └─ 진동모터
    │
    └→ WebSocket 브로드캐스트
           ↓
      [관리자 브라우저]
         (모바일/PC)
```

---

## 결정 사항

### 1. 관리자 모니터링 플랫폼: 웹 대시보드 (네이티브 모바일 앱 대신)

| 항목 | 네이티브 앱 | 웹 대시보드 |
|------|----------|----------|
| 개발 시간 | 2주+ | 3~5일 ✅ |
| 모바일/PC 접근 | 앱스토어 심사 필요 | 브라우저 URL만으로 ✅ |
| 알림 | 네이티브 푸시 | 브라우저 Notification API ✅ |
| 발표 데모 | 기기 준비 필요 | 어떤 환경에서든 즉시 시연 ✅ |
| 기존 스택 활용 | ✗ 새 언어 | ✅ Python 100% |

**결론**: Python FastAPI + WebSocket + HTML5 기반 웹 대시보드로 결정.

### 2. 작업자 피드백: 3중 출력 장치 (OLED + LED + 진동모터)

BOM에 이미 포함된 하드웨어를 활용하여 근무자에게 **즉각적인 로컬 피드백** 제공:

| 장치 | 정보 내용 | 레벨별 형태 |
|------|---------|-----------|
| **OLED SSD1306** | 실시간 피로도 %, MF, 상태 텍스트 | 텍스트 + 바 그래프 |
| **RGB LED** | 상태 색상 표시 | 초록(정상) / 노랑(경고) / 빨강(긴급) |
| **진동모터** | 촉각 알림 | 약한 1회(경고) / 강한 연속(긴급) |

### 3. 양방향 UDP 통신 구조

**기존 (원방향)**:
```
ESP32 → PC (EMG/IMU raw)
```

**변경 (양방향)**:
```
ESP32 → PC (EMG/IMU raw)
PC → ESP32 (분석 결과: fatigue_pct, mf, level)
```

ESP32는 연산 없이 **결과를 수신하여 출력만 담당** → 전력 소비 최소화, 간단한 펌웨어.

---

## 구현 완료 목록

### PC 쪽 (Python)

✅ `tools/dashboard/server.py` (FastAPI)
- UDP 수신 (EMG raw)
- SciPy를 이용한 FFT + Median Frequency 계산
- 피로도 지수 산출 및 레벨 판정
- WebSocket 브로드캐스트 (100ms 주기)
- UDP 역전송 (분석 결과 → ESP32)

✅ `tools/dashboard/static/` (웹 UI)
- 반응형 HTML5/CSS3 레이아웃 (모바일 & PC)
- 실시간 EMG 파형 그래프 (Chart.js)
- 피로도 추이 라인 차트
- 반원형 게이지 (0~100%)
- 브라우저 Push Notification API 통합
- 경고 로그 (시간, 레벨, fatigue %)

✅ `requirements.txt`
- `fastapi`, `uvicorn`, `websockets` 추가

### ESP32 펌웨어 (MicroPython)

✅ `firmware/ui/oled.py`
- SSD1306 드라이버 (I2C)
- 화면 레이아웃: 모드 + 피로도 % + 바 그래프 + MF + 상태 텍스트
- 레벨별 상태 깜박임 애니메이션 (CRITICAL)

✅ `firmware/ui/led.py`
- RGB LED PWM 제어
- 레벨별 색상 매핑 (normal/warning/critical)
- Pulse 페이드 효과 (선택사항)

✅ `firmware/ui/motor.py`
- 진동모터 PWM 제어
- 패턴: 약한 단일 펄스(경고), 강한 연속 진동(긴급)
- 레벨별 자동 실행 함수

✅ `firmware/comm/wifi.py`
- WiFi 연결 관리
- UDP 양방향 통신
  - `send_emg_data()` — EMG raw 송신
  - `send_imu_data()` — IMU 송신
  - `recv_analysis_result()` — 분석 결과 수신 (non-blocking)

### 테스트

✅ `tests/test_dashboard.py`
- FatigueAnalyzer 단위 테스트
- 신호 처리 (필터링, FFT) 검증
- 레벨 판정 임계치 검증

✅ `tests/test_oled.py`
- 피로도 → 바 너비 변환
- 상태 문자열 매핑
- 디스플레이 형식 검증

---

## 임계치 정의

| 레벨 | 조건 | OLED | LED | 진동모터 |
|------|------|------|-----|---------|
| `normal` | fatigue < 80% | "OK" | 🟢 초록 | 없음 |
| `warning` | 80% ≤ fatigue < 95% | "WARNING" | 🟡 노랑 | 약한 1회 |
| `critical` | fatigue ≥ 95% | "CRITICAL!" (깜박임) | 🔴 빨강 | 강한 연속 |

---

## 검증 시나리오

### 1. 웹 대시보드 접근

```bash
python -m tools.dashboard.server
# 터미널에 출력: http://192.168.x.x:8000
```

관리자가 같은 WiFi의 스마트폰/PC 브라우저로 URL 접속 → 대시보드 로드됨

### 2. ESP32 데이터 송수신

- ESP32가 UDP로 EMG raw 전송
- PC가 분석 후 결과를 UDP 역전송
- ESP32가 OLED + LED + 진동으로 피드백

### 3. 브라우저 알림

- 피로도 80% 도달 → 브라우저 알림 팝업 + 로그 추가
- 피로도 95% 도달 → 긴급 알림 + CRITICAL 상태

### 4. 테스트 실행

```bash
python -m pytest tests/test_dashboard.py -v
python -m pytest tests/test_oled.py -v
```

---

## 다음 단계

1. **펌웨어 통합**
   - EMG/IMU 센서 드라이버와 OLED/LED/Motor 통합
   - UDP 양방향 메인 루프 구현

2. **실제 센서 테스트**
   - ESP32 + MyoWare 2.0 + MPU6050 연결
   - 실시간 데이터 수신 및 분석 검증

3. **웹 대시보드 배포**
   - 네트워크 설정 가이드 작성
   - 대시보드 접근성 최적화 (방화벽 설정 등)

4. **성능 최적화**
   - 레이턴시 목표 50ms 이내 달성
   - 진동모터 패턴 사용자 피드백 기반 조정

---

## 변경 히스토리

- **2026-04-02**: BOM 확정, 초기 기획에서 BLE HID → WiFi UDP로 변경
- **2026-04-12**: 관리자 모니터링 시스템 기획 및 구현 완료
