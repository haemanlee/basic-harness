---
name: pr-description-generator
description: Generates a PR title and description draft (Summary + Test plan) from the PRD and the completed implementation/verification results. Use as the final wrap-up step once all pipeline gates (functional, security, integration) have passed. Produces markdown text only — never runs git commands or creates the PR itself.
---

# PR 설명 생성

파이프라인의 모든 게이트가 PASS된 뒤, PRD와 구현·검증 결과를 바탕으로 사용자가 그대로 사용할 수 있는 PR 제목/본문 초안을 작성한다.

## 입력

- 원본 PRD
- `backend-implementer`의 구현 요약 (파일 목록, 단위 테스트 목록)
- `code-verifier` / `security-reviewer` / `integration-tester`의 최종 판정 요약
- (있다면) `convention-check`의 참고 항목

## 원칙

- **실제 git 명령이나 PR 생성을 수행하지 않는다.** 텍스트 초안만 만들고, 실제로 커밋/푸시/PR 오픈은 사용자가 직접 하거나 별도로 명시적 요청해야 한다.
- PRD에 없는 내용을 지어내지 않는다 — 구현 요약과 검증 결과에 실제로 있는 내용만 반영한다.

## 출력 형식

```markdown
## PR 제목
{70자 이내, 무엇을 하는 변경인지 한 줄 요약}

## Summary
- {핵심 변경 사항 bullet 1}
- {핵심 변경 사항 bullet 2}

## Test plan
- [x] code-verifier: PASS (기능적 일치성 확인)
- [x] security-reviewer: PASS
- [x] integration-tester: PASS
- [ ] (사용자가 수동으로 추가 확인할 항목이 있다면 여기 추가)

## 참고 사항
{convention-check 결과가 있다면 여기 요약}
```
