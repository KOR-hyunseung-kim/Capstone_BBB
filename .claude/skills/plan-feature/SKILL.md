---
name: plan-feature
description: BBB 새 기능을 정의하고 스펙 문서를 생성하는 워크플로우. 기획 단계에서 호출.
disable-model-invocation: false
---

BBB 프로젝트의 새 기능을 기획합니다: **$ARGUMENTS**

다음 순서로 진행합니다:

1. `Overview.md`와 `docs/specs/` 하위 기존 스펙 문서를 읽어 현재 프로젝트 상태 파악
2. `CLAUDE.md`의 H/W 제약 규칙(경량화, BLE/WiFi 전용, 진동모터 필수) 확인
3. AskUserQuestion 툴로 다음 사항을 인터뷰:
   - 어느 동작 모드에 해당하는가? (Safety / Control / Both)
   - 사용자 입력·출력(피드백 수단)은 무엇인가?
   - 기술적으로 어려운 부분이 있는가?
   - 검증 기준(수치 기준)은 무엇인가?
4. H/W 제약에 위배되는 요소가 있으면 즉시 지적하고 대안 제시
5. `docs/specs/<feature-name>.md` 형식으로 스펙 문서 작성:
   ```
   # Feature: <기능명>
   ## 목표
   ## 동작 모드
   ## 입력 / 출력
   ## 알고리즘 개요
   ## H/W 영향 (무게·전류 변화)
   ## 검증 기준 (구체적 수치)
   ## 미결 사항
   ```
6. 스펙 완성 후 `/implement <파일경로>` 로 구현 단계 진행 안내
