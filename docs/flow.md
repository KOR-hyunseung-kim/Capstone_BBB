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
- [ ] MOSFET 회로 납땜 (만능기판, 2N7000 + 1N4148 + 100Ω)
- [ ] 점퍼선 & 배선 납땜 (EMG/IMU/LED/모터/스위치)
- [ ] 배터리 JST 커넥터 납땜
- [ ] 기본 배선 테스트 (멀티미터 도통 확인)
- [ ] 부팅 테스트 (USB 연결 → Thonny LED 확인)

---

## 관리자 모니터링 시스템 (웹 대시보드)

- [x] `2026-04-12` FastAPI + WebSocket 서버 구현 (`tools/dashboard/server.py`)
- [x] `2026-04-12` 웹 대시보드 UI (HTML/CSS/JS) (`tools/dashboard/static/`)
- [x] `2026-04-12` SSD1306 OLED 디스플레이 드라이버 (`firmware/ui/oled.py`)
- [x] `2026-04-12` RGB LED 제어 모듈 (`firmware/ui/led.py`)
- [x] `2026-04-12` 진동모터 제어 모듈 (`firmware/ui/motor.py`)
- [x] `2026-04-12` UDP 양방향 통신 구현 (`firmware/comm/wifi.py`)
- [ ] 웹 대시보드 브라우저 테스트 (모바일 & PC 반응형)
- [ ] 브라우저 Push Notification 권한 요청 및 알림 테스트
- [ ] 실제 ESP32 데이터로 대시보드 end-to-end 테스트

---

## 펌웨어 (ESP32-S3 MicroPython)

- [x] `2026-04-16` 개발 환경 구축 가이드 (Thonny, MicroPython 플래싱)
- [x] `2026-04-16` MyoWare 2.0 ADC 드라이버 (`firmware/sensor/emg.py`, 1kHz 샘플링)
- [ ] WiFi UDP 송수신 기본 통신
- [ ] MPU6050 I2C 드라이버 (`firmware/sensor/imu.py`)
- [ ] 진동모터 GPIO PWM 제어 (`firmware/ui/motor.py`) ← 2026-04-12 완료
- [ ] RGB LED 제어 (`firmware/ui/led.py`) ← 2026-04-12 완료
- [ ] OLED SSD1306 디스플레이 (`firmware/ui/oled.py`) ← 2026-04-12 완료
- [ ] 택트 스위치 인터럽트 (모드 전환)
- [ ] Safety / Control 모드 전환 로직

---

## DSP 알고리즘 (노트북 Python)

- [ ] WiFi UDP 수신 서버 (`tools/receiver.py`)
- [ ] EMG Band-pass 필터 (20~500Hz)
- [ ] FFT + Median Frequency 추출
- [ ] 피로도 판정 로직 (80% / 95% 임계치)
- [ ] IMU Complementary Filter (pitch / roll)
- [ ] pyautogui 커서 이동 · 클릭 제어
- [ ] WiFi 명령 송신 (진동·LED 제어)

---

## 통합 & QA

- [ ] Safety Mode 엔드-투-엔드 테스트
- [ ] Control Mode 엔드-투-엔드 테스트
- [ ] pytest 단위 테스트 커버리지 80%+
- [ ] 성능 검증 (레이턴시 <50ms, 오검출 <5%, 드리프트 <2px/s)
- [ ] 사용자 착용 테스트 및 피드백 반영

---

## 마무리

- [ ] 최종 발표 자료 업데이트
- [ ] 시연 시나리오 리허설
- [ ] `2026-06-12` 최종 발표 & 라이브 시연
