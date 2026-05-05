# 기획 보강 — 시나리오 현실화 및 제품 필요성 근거 강화

**날짜**: 2026-04-02  
**작업자**: planner agent / Human  
**관련 파일**: `docs/specs/project-overview-v2.md`, `docs/progress.md`

## 요약
BOM 작성 완료 후 기획 약점 보완. 추상적 시나리오를 구체적 페르소나·타임라인으로 재작성.
국내 근골격계 질환 통계 데이터 추가, 기존 해결책 한계 비교표 작성.
`docs/progress.md` 신규 생성 (프로젝트 전체 흐름 현황 관리 파일).

## 결정 사항

### 기획 보강 내용
| 항목 | 이전 | 이후 |
|------|------|------|
| 타겟 페르소나 | 직군만 언급 (물류, 정비사) | 이름·나이·근무환경 포함 구체적 인물 |
| 시나리오 | 단순 설명 (2~3줄) | 타임라인 표 + Before/After 비교 |
| 제품 필요성 근거 | 없음 | 고용노동부·안전보건공단 통계 수치 |
| 기존 해결책 비교 | 없음 | 6가지 대안 한계 분석 표 |
| 듀얼 모드 근거 | 없음 | 센서 재활용 + 맥락 전환 논리 |

### 페르소나 정의
- **페르소나 A**: 김지훈 (28세) — 수도권 물류 창고, 하루 500회 박스 하역, Safety Mode 타겟
- **페르소나 B**: 이수연 (34세) — 항공 MRO 정비, 매뉴얼 조회 빈번, Control Mode 타겟

### docs/progress.md 신설
- 프로젝트 전체 흐름에서 현재 단계를 한눈에 파악할 수 있는 living document
- 큰 업무(BOM, 핀맵, 펌웨어, DSP, QA) 완료 시 덮어쓰기 방식으로 최신화
- `docs/history/*.md`는 세부 기록용, `docs/progress.md`는 현재 상태 요약용으로 역할 분리

## 변경된 파일
- `docs/specs/project-overview-v2.md` — 신규 생성 (기획 보강 전체 내용)
- `docs/progress.md` — 신규 생성 (프로젝트 진행 현황 living document)
- `docs/history/2026-04-02-planning-review.md` — 이 파일

## 다음 단계
1. MyoWare 2.0 주문 선행 (SparkFun DEV-21267 × 2)
2. 국내 부품 주문 (디바이스마트/ICBANQ)
3. 부품 수령 후 핀맵 정의 → `docs/history/YYYY-MM-DD-pinmap.md`
4. 발표 자료에 시나리오 상세 내용 반영 검토
