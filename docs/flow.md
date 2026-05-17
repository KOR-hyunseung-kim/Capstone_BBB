# BBB 개발 진행 Flow

> 완료 항목에는 날짜 태그 추가. 이 파일은 진행될 때마다 overwrite.

---

## 기획 & 설계

- [x] `2026-04-02` 프로젝트 개요 및 아키텍처 확정 (WiFi 통신, 노트북 연산)
- [x] `2026-04-02` 기획 보강 — 페르소나·시나리오·근거 자료 (`docs/specs/project-overview-v2.md`)
- [x] `2026-04-02` 발표 자료 제작 (`docs/01_presentation/presentation.html`)
- [x] `2026-04-02` H/W BOM 작성 (`docs/02_HW/bom.md`)
- [x] `2026-04-02` 회로 설계 결정 (MOSFET 2N7000, 만능기판, 배터리 직결)
- [x] `2026-04-03` 과제 제안서 작성 (개요·수행방법·기대효과) (`docs/history/2026-04-03-과제-제안서.md`)

---

## H/W 준비

- [x] MyoWare 2.0 주문 (SparkFun DEV-21267 × 2, 해외 배송)
- [x] 국내 부품 주문 (XIAO ESP32-S3, MPU6050, 배터리 JST 1.25mm 등)
- [x] 부품 수령 확인
- [x] `2026-05-05` 핀맵 정의 & 회로도 작성 (`docs/history/2026-05-05-pinmap-and-circuits.md`)
- [x] `2026-05-17` H/W 최종 스펙 문서 작성 (`docs/02_HW/HW_SPEC.md`)
- [ ] MOSFET 회로 납땜 (만능기판, 2N7000 + 1N4148 + 100Ω)
- [ ] 점퍼선 & 배선 납땜 (EMG/IMU/LED/모터/스위치)
- [ ] 배터리 JST 커넥터 납땜
- [ ] 기본 배선 테스트 (멀티미터 도통 확인)
- [ ] 부팅 테스트 (USB 연결 → Thonny LED 확인)

---

## WiFi 통신 & 관리자 모니터링

- [x] `2026-04-12` FastAPI + WebSocket 서버 구현 (`tools/dashboard/server.py`)
- [x] `2026-04-12` 웹 대시보드 UI (HTML/CSS/JS) (`tools/dashboard/static/`)
- [x] `2026-05-06` WiFi UDP 송수신 기본 통신 (firmware ↔ PC)
- [x] `2026-05-06` PC 수신 서버 (`tools/receiver.py`)
- [x] `2026-05-06` MicroPython WiFi 버그 픽스 (`firmware/comm/wifi.py`)
- [ ] 웹 대시보드 브라우저 테스트 (모바일 & PC 반응형)
- [ ] 실시간 데이터 시각화 (차트, 신호파형)
- [ ] PC → ESP32 원격 제어 (모드 전환, LED 색상)

---

## Safety Mode (EMG 기반 피로도 모니터링)

- [x] `2026-04-16` MyoWare 2.0 ADC 드라이버 (`firmware/sensor/emg.py`, 1kHz 샘플링)
- [x] `2026-05-06` EMG 신호 처리 알고리즘 (RMS 계산) (`firmware/algo/emg_processor.py`)
- [x] `2026-05-06` Calibration 로직 (1분 기준값 설정)
- [x] `2026-05-06` 피로도 판정 (≥90% 정상, 70~90% 주의, <70% 경고)
- [x] `2026-05-06` 진동모터 피드백 (약한/강한 강도) (`firmware/ui/motor.py`)
- [x] `2026-05-06` 단위/통합 테스트 (16/16 pass) (`tests/test_emg_fatigue.py`)
- [x] `2026-05-06` Safety Mode 메인 루프 (`firmware/main.py`)
- [x] `2026-05-06` RGB LED 제어 (정상 🟢 / 주의 🟡 / 경고 🔴) (`firmware/ui/led.py`)
- [x] `2026-05-06` 핀맵 중앙화 설정 파일 (`firmware/config.py`)
- [x] `2026-05-08` OLED 디스플레이 통합 (SSD1306 드라이버 내장, I2C 안정화) (`firmware/ui/oled.py`)
- [x] `2026-05-08` Calibration 중 OLED 진행률 표시 (`firmware/algo/emg_processor.py`)
- [x] `2026-05-08` OLED show_message(), show_progress() 메서드 추가
- [x] `2026-05-17` Safety Mode 재구현 (독립 실행형) (`firmware/safety_mode.py`)
- [x] `2026-05-17` 진동 패턴 최적화 (긴 텀 vs 짧은 텀)
- [x] `2026-05-17` 모드 전환 버튼 통합 (GPIO21)
- [ ] 실제 하드웨어 통합 테스트 (납땜 후)
- [ ] 사용자 피로도 보정 (개인차 캘리브레이션)

---

## Control Mode (IMU + EMG 기반 마우스 제어)

- [x] `2026-05-12` Kalman Filter 구현 (1D/3D/적응형) (`firmware/algo/kalman_filter.py`)
- [x] `2026-05-12` MPU6050 I2C 드라이버 (`firmware/sensor/imu.py`)
- [x] `2026-05-12` ICM-20602 드라이버 (성능 업그레이드) (`firmware/sensor/icm20602.py`)
- [x] `2026-05-12` 실시간 기울기 계산 (Pitch/Roll)
- [x] `2026-05-12` Complementary Filter (자이로+가속도 융합)
- [x] `2026-05-12` MicroPython 호환 테스트 (14/14 pass) (`firmware/test_kalman_micropython.py`)
- [x] `2026-05-12` 커서 이동 알고리즘 (Raw ax, ay 기반) (`firmware/algo/control.py`)
- [x] `2026-05-12` EMG Click 감지 (`firmware/algo/control.py`)
- [x] `2026-05-12` Control Mode 메인 루프 (50Hz) (`firmware/control_main.py`)
- [x] `2026-05-12` 자동 캘리브레이션 (50개 샘플)
- [x] `2026-05-12` OLED 실시간 표시 (10Hz)
- [x] `2026-05-12` 완전 사용 가이드 작성 (`docs/CONTROL_MODE_GUIDE.md`)
- [x] `2026-05-17` Control Mode 재구현 (Complementary Filter 기반) (`firmware/control_mode.py`)
- [x] `2026-05-17` IMU 캘리브레이션 (가속도 + 자이로)
- [x] `2026-05-17` EMG 스파이크 클릭 감지 (ADC > 3500)
- [ ] BLE HID Mouse 구현 (마우스 이동 / 클릭)
- [ ] Control Mode 전체 하드웨어 통합 테스트

---

## 통합 & QA

- [x] `2026-05-17` Safety Mode & Control Mode 듀얼 모드 구현 완료
- [x] `2026-05-17` 모드 전환 로직 구현 (GPIO21 버튼, 메뉴 시스템)
- [ ] Safety Mode 엔드-투-엔드 테스트 (실제 팔 착용)
- [ ] Control Mode 엔드-투-엔드 테스트 (마우스 제어)
- [ ] pytest 단위 테스트 커버리지 80%+ (현재: EMG 알고리즘 완료)
- [ ] 성능 검증 (반응성, 오작동률, 배터리 지속시간)
- [ ] 사용자 착용 테스트 및 피드백 반영

---

## 마무리

- [ ] 최종 발표 자료 업데이트
- [ ] 시연 시나리오 리허설 (Safety → Control 모드 전환 시연)
- [ ] `2026-06-12` 최종 발표 & 라이브 시연
