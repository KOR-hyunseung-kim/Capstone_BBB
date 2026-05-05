---
name: implement
description: BBB 스펙 문서를 기반으로 펌웨어 코드와 테스트를 구현하는 워크플로우.
disable-model-invocation: false
---

BBB 스펙에 따라 구현을 진행합니다: **$ARGUMENTS**

다음 순서로 진행합니다:

1. 지정된 스펙 파일(`$ARGUMENTS`)을 읽어 요구사항과 검증 기준 파악
2. `firmware/` 하위 관련 모듈 코드를 읽어 기존 패턴 확인
3. **테스트 먼저 작성** — `tests/test_<module>.py`에 스펙의 검증 기준을 pytest 케이스로 변환
4. 코딩 규칙 준수하며 구현:
   - 줄 길이 ≤ 88자, type hints, Google docstring
   - 모듈 배치: `sensor/` `algo/` `comm/` `ui/` 단일 책임
   - MicroPython 호환 코드 (numpy/scipy 금지)
   - `SIM_MODE=True` 환경변수로 하드웨어 없이 테스트 가능하도록
5. 구현 완료 후 테스트 실행:
   ```bash
   python -m pytest tests/ -v
   black --check firmware/
   ```
6. 테스트 실패 시 근본 원인 분석 후 수정 — 테스트를 변경하지 말 것
7. 모든 테스트 통과 후 `/run-qa`로 QA 단계 진행 안내
