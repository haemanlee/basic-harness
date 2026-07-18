# techedu — PRD 기반 백엔드 구현 파이프라인

이 프로젝트는 PRD/기획서를 입력으로 받아 **검토 → 구현 → 기능 검증 → 보안/통합 검증 → 마무리**를 자동으로 오케스트레이션합니다. 오케스트레이션은 아래 "리더-팀원 구조"와 "공유 작업 목록" 규칙을 따릅니다.

## 트리거

사용자가 PRD/기획서 파일을 제공하면(첨부, 경로 언급, 또는 붙여넣기) 아래 파이프라인을 자동으로 시작합니다. 사용자가 특정 단계만 명시적으로 요청한 경우 해당 단계만 수행합니다.

## 리더-팀원 구조

- **리더는 이 CLAUDE.md를 읽고 파이프라인을 진행하는 최상위 세션 그 자체**입니다. 별도의 "leader" 에이전트 파일을 만들지 않습니다 — 리더를 서브에이전트로 분리하면 여러 인스턴스가 동시에 생겨 "리더는 하나"라는 전제가 깨질 수 있습니다. 최상위 세션은 대화당 하나뿐이므로 이 자체로 리더 유일성이 보장됩니다.
- **팀원(5개 에이전트: `prd-completion-assistant`, `backend-implementer`, `code-verifier`, `security-reviewer`, `integration-tester`)은 `Agent`/`SendMessage` 도구를 갖지 않습니다.** 이는 프롬프트 지시가 아니라 tools 목록에서 아예 빼서 구조적으로 강제합니다. 그 결과 팀원은 다른 팀원을 스폰하거나 팀원끼리 직접 메시지를 보낼 수 없고, 모든 소통은 리더를 거칩니다.
- **팀원 결과는 리더만 읽고, 리더가 걸러서 다음 팀원에게 전달합니다.** 예를 들어 `code-verifier`의 FAIL 피드백을 `backend-implementer`에게 그대로 전달하지 않고, 리더가 관련 있는 내용만 추려 새 메시지로 구성해 전달합니다. 팀원이 다른 팀원의 원본 출력을 직접 보는 일은 없습니다.
- **팀원은 하나의 파이프라인 실행(하나의 PRD를 완료 보고 또는 에스컬레이션까지 처리하는 사이클) 동안 `Agent`로 최초 1회만 스폰됩니다.** 이후 같은 실행 내에서 재작업·재검증 등 후속 요청은 새로 스폰하지 않고 **`SendMessage`로 이름을 지정해 같은 인스턴스에 이어서** 전달합니다. 스폰된 에이전트는 자신의 이전 작업 맥락(무엇을 구현했는지, 어떤 지적을 받았는지)을 그대로 유지한 채 이어받으므로, 매번 처음부터 설명할 필요가 없습니다.
- 완전히 새로운 PRD로 파이프라인을 다시 시작할 때만 팀원을 새로 스폰합니다.
- 스킬(`prd-review`, `convention-check`, `pr-description-generator`, `retry-postmortem`)은 별도 인스턴스가 아니라 **리더가 자신의 컨텍스트에서 직접 수행하는 절차**입니다. 팀원과 달리 SendMessage 대상이 아닙니다.

## 공유 작업 목록

- 리더는 파이프라인 시작 시 `TaskCreate`로 아래 태스크를 만듭니다 (필요한 것만 — 예: critical PRD 이슈가 없으면 "PRD 보완 초안" 태스크는 생성하지 않음):

| 태스크 | owner |
|---|---|
| PRD 완전성 검토 | 리더 (직접 수행) |
| PRD 보완 초안 (critical 있을 때만) | `prd-completion-assistant` |
| 백엔드 구현 | `backend-implementer` |
| 기능 검증(3a) | `code-verifier` |
| 보안 검증(3b) | `security-reviewer` |
| 통합 테스트(3b) | `integration-tester` |
| 마무리 | 리더 (직접 수행) |

- 리더는 팀원을 `Agent`/`SendMessage`로 호출할 때 **해당 팀원이 갱신해야 할 태스크 ID를 함께 전달**합니다.
- **팀원은 진행 상황을 리더에게 프로즈로 보고하는 것과 별개로, 자신의 태스크를 직접 `TaskUpdate`로 기록합니다.** 작업을 시작하면 `in_progress`로, 마치면 `completed`로 전환하고, `metadata`에 시도 회차(예: `{"attempt": 2, "verdict": "FIX"}`)를 남깁니다. 이는 리더가 대화 내용을 요약·압축하더라도 재시도 횟수와 판정 이력이 태스크 목록에 구조적으로 남도록 하기 위함입니다.
- 리더는 재시도 여부를 판단할 때 팀원의 텍스트 출력뿐 아니라 **`TaskGet`/`TaskList`로 태스크 metadata를 함께 확인**합니다. 둘이 어긋나면(예: 텍스트는 2회차라는데 metadata는 1회차) 태스크 목록 쪽을 신뢰하고 팀원에게 확인을 요청합니다.
- 에스컬레이션(5단계)에서 `retry-postmortem`은 대화 기록이 아니라 **태스크 목록의 metadata 이력을 1차 근거**로 시도별 판정을 정리합니다.

## 파이프라인

### 1단계 — PRD 완전성 검토 (`prd-review` 스킬, 리더가 직접 수행)

- `prd-review` 스킬로 PRD의 완전성을 검토하고 심각도별 이슈 목록을 받는다.
- **Critical 이슈가 있으면**: 파이프라인을 여기서 중단하고 "PRD 보완 초안" 태스크를 만든 뒤 `prd-completion-assistant`를 `Agent`로 스폰해 누락 항목별 보완 초안을 제시한다. 초안은 자동으로 PRD에 반영되지 않으며, 사용자가 검토·반영한 뒤 PRD를 다시 제공하면 1단계를 재실행한다 (같은 PRD의 재보완 요청이면 새 인스턴스 대신 `SendMessage`로 기존 `prd-completion-assistant`에 이어서 요청한다).
- Critical 이슈가 없으면 (major/minor는 참고용으로 함께 제시하고) 2단계로 진행한다.

### 2단계 — 구현 (`backend-implementer` 팀원)

- "백엔드 구현" 태스크를 만들고, 완전성 검토를 통과한 PRD를 담아 `backend-implementer`를 `Agent`로 최초 스폰한다.
- 재작업 루프로 되돌아온 경우, 리더가 3a/3b 피드백 중 관련 있는 부분만 추려 **같은 `backend-implementer` 인스턴스에 `SendMessage`로 전달**한다 (새로 스폰하지 않음 — 이전 구현 맥락을 유지해야 국소 수정이 가능하다).

### 3a단계 — 기능 검증 (`code-verifier` 팀원)

- "기능 검증(3a)" 태스크를 만들고 `code-verifier`를 최초 스폰(이후는 `SendMessage`로 이어감)해, 구현 결과가 PRD 요구사항을 기능적으로 충족하는지 검증한다. 판정은 **PASS / FAIL** 이진값이다.
- **FAIL** → 피드백을 리더가 걸러 `backend-implementer`에게 `SendMessage`로 전달하고 2단계부터 재실행한다. 이 루프 전용 재시도 카운터를 사용하며, **3회를 초과하면 5단계(에스컬레이션)로 이동**한다.
- **PASS** → 3b단계로 진행한다.
- `code-verifier`는 매 실행마다 출력과 태스크 metadata 양쪽에 "시도 회차(N/3)"를 남긴다. 재시도 횟수 판단은 태스크 metadata를 우선한다.

### 3b단계 — 보안/통합 검증 (`security-reviewer` + `integration-tester` 병렬)

- 3a단계를 통과한 구현에 대해서만 실행한다 (기능적으로 틀린 코드에 비용이 큰 검증을 낭비하지 않기 위함).
- "보안 검증(3b)", "통합 테스트(3b)" 태스크를 만들고 두 팀원을 각각 최초 스폰(이후는 `SendMessage`)해 병렬로 실행한다. 판정은 **PASS / FIX / REDO** 3단계다.
- **REDO** (치명적 취약점, 또는 핵심 시나리오 다수 실패) → 리더가 전체 재작업 피드백을 `backend-implementer`에게 `SendMessage`로 전달하고 **3a단계부터** 재실행한다.
- **FIX** (국소적 패치로 해결 가능) → 리더가 경량 패치 요청을 `backend-implementer`에게 `SendMessage`로 전달하고 **3b단계만** 재실행한다.
- FIX/REDO 어느 쪽이든 이 단계 전용 재시도 카운터를 1 증가시키며, **2회를 초과하면 5단계(에스컬레이션)로 이동**한다.
- **PASS** (둘 다 통과) → 4단계로 진행한다.
- `security-reviewer`/`integration-tester`도 매 실행마다 출력과 태스크 metadata 양쪽에 "시도 회차(N/2)"를 남긴다. 두 카운터(3a용 N/3, 3b용 N/2)는 서로 다른 숫자이므로 혼동하지 않는다.

### 4단계 — 마무리 (리더가 직접 수행)

- `convention-check` 스킬을 1회 실행한다. 결과는 **참고용이며 파이프라인을 막지 않는다.**
- `pr-description-generator` 스킬로 PR 제목/본문 초안을 생성한다. **실제 git/PR 조작은 하지 않는다** — 텍스트 산출물만 사용자에게 제시한다.
- "마무리" 태스크를 completed로 전환하고, 구현 요약 + 3a/3b 검증 결과 + 컨벤션 참고사항 + PR 초안을 묶어 사용자에게 완료 보고한다.

### 5단계 — 에스컬레이션 (리더가 직접 수행)

- 3a단계 재시도 3회 초과, 또는 3b단계 재시도 2회 초과 시 도달한다.
- `retry-postmortem` 스킬로 태스크 목록의 metadata 이력을 근거 삼아 지금까지의 시도 이력과 반복 패턴, 핵심 쟁점을 간결하게 정리해 사용자에게 전달한다. 원본 로그를 그대로 나열하지 않는다.
- 자동 재시도는 여기서 멈추고, 다음 진행 여부는 사용자가 판단한다.

## 파이프라인 다이어그램

```
                         ┌─────────────── 리더 (최상위 세션, 유일) ───────────────┐
                         │  Agent: 팀원 최초 스폰 · SendMessage: 같은 팀원에 이어서 전달 │
                         │  TaskCreate/TaskGet/TaskList: 공유 작업 목록 관리          │
                         └───────────────────────┬───────────────────────────────┘
                                                  │ (팀원끼리는 직접 연락 불가 — Agent/SendMessage 없음)
PRD 입력
  │
  ▼
[1] prd-review 스킬(리더) ──critical 있음──▶ [1a] prd-completion-assistant 팀원
  │ critical 없음                              (보완 초안 제시, 자동 반영 안 함)
  ▼                                            │
[2] backend-implementer 팀원 ◀─────────────────┘ 사용자가 PRD 반영 후 [1] 재실행
  │ (구현 + 단위테스트, 태스크 직접 갱신)
  ▲
  │ FAIL, 재시도 ≤3 (SendMessage로 이어서 전달)
  │
[3a] code-verifier 팀원 (기능 검증, PASS/FAIL)
  │ FAIL, 재시도 >3 ──▶ [5] 에스컬레이션
  │ PASS
  ▼
[3b] security-reviewer + integration-tester 팀원 (병렬, PASS/FIX/REDO)
  │ FIX  ──▶ [2]로 경량 패치 요청, [3b]만 재실행 ─┐
  │ REDO ──▶ [2]로 전체 재작업 요청, [3a]부터 재실행 ┤ 재시도 ≤2
  │                                              │ 재시도 >2 ──▶ [5]
  │ PASS
  ▼
[4] 마무리(리더): convention-check(비차단) + pr-description-generator
  │
  ▼
완료 보고

[5] 에스컬레이션(리더): retry-postmortem(태스크 metadata 근거) → 사용자 판단 대기
```

## 각 컴포넌트

| 컴포넌트 | 위치 | 책임 | 통신 방식 |
|---|---|---|---|
| `prd-review` 스킬 | `.claude/skills/prd-review/SKILL.md` | PRD 완전성 검토, 심각도별 이슈 목록 출력 | 리더가 직접 수행 |
| `prd-completion-assistant` 팀원 | `.claude/agents/prd-completion-assistant.md` | Critical 누락 항목 보완 초안 제시 (PRD 직접 수정 안 함) | 리더가 Agent 최초 스폰 → SendMessage로 이어감 |
| `backend-implementer` 팀원 | `.claude/agents/backend-implementer.md` | Spring 구현 + 단위 테스트 작성 | 리더가 Agent 최초 스폰 → SendMessage로 이어감 |
| `code-verifier` 팀원 | `.claude/agents/code-verifier.md` | PRD 대비 기능적 일치성 검증(PASS/FAIL), 코드 직접 수정 금지 | 리더가 Agent 최초 스폰 → SendMessage로 이어감 |
| `security-reviewer` 팀원 | `.claude/agents/security-reviewer.md` | 보안 취약점 검증(PASS/FIX/REDO), 코드 직접 수정 금지 | 리더가 Agent 최초 스폰 → SendMessage로 이어감 |
| `integration-tester` 팀원 | `.claude/agents/integration-tester.md` | 통합/E2E 테스트 작성·실행(PASS/FIX/REDO), 프로덕션 코드 수정 금지 | 리더가 Agent 최초 스폰 → SendMessage로 이어감 |
| `convention-check` 스킬 | `.claude/skills/convention-check/SKILL.md` | 코드 컨벤션 점검 (참고용, 비차단) | 리더가 직접 수행 |
| `pr-description-generator` 스킬 | `.claude/skills/pr-description-generator/SKILL.md` | PR 제목/본문 초안 생성 (git/PR 조작 없음) | 리더가 직접 수행 |
| `retry-postmortem` 스킬 | `.claude/skills/retry-postmortem/SKILL.md` | 에스컬레이션 시 시도 이력 요약 | 리더가 직접 수행 |

## 원칙

- **리더는 하나뿐이다.** 최상위 세션 자체가 리더 역할을 하며, 별도 리더 에이전트를 스폰하지 않는다.
- **팀원끼리는 직접 연락하지 않는다.** `Agent`/`SendMessage` 도구를 팀원에게 주지 않는 것으로 구조적으로 강제한다. 모든 정보 교환은 리더가 중계한다.
- **팀원은 파이프라인 실행당 한 번만 스폰하고, 이후는 SendMessage로 같은 인스턴스에 이어간다.** 매번 새로 스폰하면 이전 작업 맥락(무엇을 왜 그렇게 했는지)이 유실되어 재작업 품질이 떨어진다.
- **진행 상황은 팀원이 공유 작업 목록에 직접 기록한다.** 리더가 프로즈 보고를 듣고 대신 태스크를 갱신하는 것이 아니라, 팀원 자신이 `TaskUpdate`로 상태와 시도 회차를 남긴다. 이는 대화 압축·요약에도 살아남는 구조적 기록이다.
- 각 컴포넌트는 자신의 책임 범위를 벗어나지 않는다 — `backend-implementer`는 스스로를 검증하지 않고, `code-verifier`/`security-reviewer`/`integration-tester`(테스트 코드 제외)는 프로덕션 코드를 직접 고치지 않는다.
- `prd-completion-assistant`는 PRD를 직접 수정하지 않는다 — 초안 제안과 실제 반영은 항상 분리한다.
- `convention-check`는 파이프라인을 막지 않는다. `pr-description-generator`는 텍스트 산출물만 만들 뿐 실제 git/PR 조작을 하지 않는다.
- 단계를 건너뛰지 않는다. Critical 이슈가 있는 PRD로 구현을 시작하지 않으며, 3a(기능)를 통과하지 못한 구현으로 3b(보안/통합)를 실행하지 않는다.
- 재작업 루프는 무한 반복하지 않는다 — 3a는 3회, 3b는 2회를 넘으면 반드시 사람에게 넘긴다. 두 루프의 재시도 카운터는 서로 독립적으로 추적하며, 태스크 metadata를 근거로 판단한다.
- **"코드를 직접 수정하지 않는다"는 지시는 프롬프트만으로는 완전히 강제되지 않는다** (검증 팀원들도 `Bash`를 갖고 있어 기술적으로는 파일을 바꿀 수 있음). 이를 보완하기 위해 `code-verifier`/`security-reviewer`/`integration-tester`는 작업 종료 직전 `git status --short`(또는 `git diff --stat`)로 자신이 건드린 파일이 없는지(또는 `integration-tester`의 경우 테스트 경로 밖을 건드리지 않았는지) 스스로 확인해 결과를 출력에 포함한다. 오케스트레이터(리더)는 이 자기 검증 결과에 "예상치 못한 변경"이 보고되면 즉시 사용자에게 알리고 다음 단계로 진행하지 않는다.
