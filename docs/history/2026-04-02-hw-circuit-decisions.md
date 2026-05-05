# H/W 회로 설계 결정 및 발표 자료 업데이트

**날짜**: 2026-04-02  
**작업자**: hw-architect agent / Human  
**관련 파일**: `docs/02_HW/bom.md`, `docs/01_presentation/presentation.html`

## 요약
진동모터 드라이버 모듈 제거 → MOSFET 직접 회로 방식 확정.
납땜 용이한 2N7000(TO-92) 선택, 만능기판 추가.
배터리 3.7V 직결로 EMG ADC 노이즈 분리.
발표 자료를 개선된 기획(WiFi 아키텍처, 시나리오 강화)에 맞춰 전면 업데이트.

## 결정 사항

### 진동모터 회로 방식
| 항목 | 결정 | 이유 |
|------|------|------|
| 방식 | 직접 회로 (모듈 미사용) | 경량화·소형화. 모듈 PCB 기판 무게/부피 제거 |
| MOSFET | 2N7000 (TO-92) | 핀 간격 2.54mm → 손납땜 용이. IRLML6244(SOT-23) 대비 작업성 우수 |
| 납땜 기판 | 만능기판 70×90mm 잘라 사용 | 브레드보드 접촉 불량 방지, 진동 환경 내구성 |
| 모터 전원 | 배터리 3.7V 직결 | 3.3V LDO 라인과 분리 → EMG ADC 노이즈 감소, LDO 부하 감소 |

### 회로 구성 (확정)
```
배터리 3.7V ─────────── Motor (+)
                            │
                       [1N4148] (역방향 병렬, flyback 보호)
                            │
                      Motor (-) ── 2N7000 Drain
GPIO ──[100Ω]──────────── 2N7000 Gate
                           2N7000 Source ── GND (배터리 - 공통)
```

### RGB LED
- 모듈 유지 결정 (저항 내장 모듈, GPIO 3핀 직결)
- discrete 구성 가능하나 모듈 가격(₩500) 저렴하고 단순하여 그대로 유지

### 전원 버스 구조
```
배터리 (+) ──┬── XIAO BAT 핀 (LDO → 3.3V, 센서·MCU)
              └── Motor (+) (MOSFET 회로)

배터리 (-) ──┬── XIAO GND
              └── MOSFET Source
```
만능기판 가장자리에 + 버스 / GND 버스 라인 구성.

### 발표 자료 업데이트 (presentation.html)
| 슬라이드 | 변경 내용 |
|---------|---------|
| Slide 1 | "BLE HID" → "WiFi" 배지 및 설명 |
| Slide 2 | 근피로 카드에 직업병 70% 통계, 기존 해결책 한계 추가 |
| Slide 3 | Control Mode → WiFi + pyautogui 방식으로 업데이트 |
| Slide 4 | 배터리 300mAh → 500mAh, Housing(3D Print) → Wiring(와이어링 조립) |
| Slide 6 | Control Mode 플로우 → WiFi UDP + pyautogui |
| Slide 7 | 물류 창고 하역 작업 상황 구체화, 피로 자각 없이 진행 강조 |
| Slide 8 | 정비 작업 매뉴얼 조회 상황 구체화, 15초→2초 수치 비교 |
| Slide 9 | "BLE HID + 하우징" → "WiFi 통신 + 배선 조립" |
| Slide 10 | "표준 BLE HID" → "WiFi 실시간 제어" |

## 변경된 파일
- `docs/02_HW/bom.md` — MOSFET 2N7000 교체, 만능기판 추가, 배터리 직결 방식 업데이트, 총 예산 ~₩233,000
- `docs/01_presentation/presentation.html` — WiFi 아키텍처·시나리오·BOM 반영 전면 업데이트
- `docs/history/2026-04-02-hw-circuit-decisions.md` — 이 파일

## 다음 단계
1. MyoWare 2.0 주문 선행 (SparkFun DEV-21267 × 2)
2. 국내 부품 주문 (XIAO ESP32-S3, MPU6050, 배터리, 2N7000, 만능기판 등)
3. 부품 수령 후 핀맵 정의 → `docs/history/YYYY-MM-DD-pinmap.md`
4. 만능기판에 MOSFET 회로 납땜 및 동작 테스트
