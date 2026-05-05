---
name: run-qa
description: BBB 테스트 실행, 성능 검증, 버그 리포트 생성 워크플로우.
disable-model-invocation: true
---

BBB QA 프로세스를 실행합니다.

1. 전체 테스트 스위트 실행:
   ```bash
   python -m pytest tests/ -v --cov=firmware --cov-report=term-missing
   black --check firmware/ tools/
   ```

2. 테스트 결과 분석:
   - 실패한 테스트 → 근본 원인 파악 → `docs/bugs/` 에 버그 리포트 생성
   - 커버리지 80% 미만 모듈 → 누락된 테스트 케이스 목록 작성

3. 성능 기준 확인 (통합 테스트 결과 기준):
   | 항목 | 기준 | 통과 여부 |
   |------|------|-----------|
   | 센서→BLE 레이턴시 | < 50ms | ? |
   | EMG Spike 오검출 | < 5% | ? |
   | IMU 커서 드리프트 | < 2px/s | ? |
   | BLE 재연결 시간 | < 3초 | ? |

4. QA 리포트를 `docs/qa-report-<날짜>.md`에 저장:
   - 통과/실패 항목 요약
   - 발견된 버그 목록 (심각도 포함)
   - 다음 스프린트 권고 사항

5. 모든 Critical/Major 버그 해결 후 `fw-developer` 에이전트에 수정 요청
