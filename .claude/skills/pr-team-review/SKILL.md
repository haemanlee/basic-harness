---
name: pr-team-review
description: Orchestrates a phased peer-agent team (shared code-verifier as a solo functional gate, then the dedicated pr-security-reviewer + pr-integration-tester as direct peers) to review an arbitrary PR or diff — independent of this repo's PRD→backend-implementation pipeline. Use when the user asks to review a PR, review a diff, or check a pull request for correctness/security/integration issues, by PR number, branch, or pasted diff. Distinct from prd-review (PRD completeness) and convention-check (style) — this reviews already-written code for functional correctness, security, and integration issues.
---

# PR 팀 리뷰 (Phase 분할 피어 팀)

이 스킬은 CLAUDE.md의 PRD→백엔드 구현 파이프라인과는 **독립적인 진입점**이다. PRD 존재 여부와 무관하게 임의의 PR/diff를 리뷰한다. 이 스킬을 실행하는 세션이 "리더"이며, 실행 중에는 이 문서가 오케스트레이션 규칙이다.

**어떤 에이전트를 쓰는가 (중요):**
- Phase 1은 파이프라인과 공유하는 **`code-verifier`**(읽기 전용, `SendMessage` 없음)를 그대로 쓴다.
- Phase 2는 이 스킬 **전용 에이전트 `pr-security-reviewer` / `pr-integration-tester`**를 쓴다. 이들은 PRD 파이프라인의 `security-reviewer`/`integration-tester`와 **별개 파일**이다 — 파이프라인 리뷰어는 `SendMessage`를 구조적으로 갖지 않아 리더-중계만 하고, 이 스킬의 피어들만 `SendMessage`를 갖는다. 이렇게 분리함으로써 "일반 PRD 실행에서 리뷰어가 리더를 우회할 수 없다"는 구조적 보장을 유지한다. (파이프라인의 `security-reviewer`/`integration-tester`를 이 스킬에서 쓰지 않는다.)

기존 파이프라인의 [3a]/[3b]는 허브-앤-스포크(모든 교신이 리더 경유)지만, 이 스킬은 Phase 2에서 두 피어가 서로 `SendMessage`로 직접 통신하는 **피어 팀**이다. 리더는 매 단계를 지시하지 않고, 완료 보고를 통합하고 유휴/에러 상황에만 개입한다.

## 언제 실행하는가

- 사용자가 PR 번호/브랜치/diff를 주며 "리뷰해줘", "검토해줘", "PR 봐줘" 등을 요청할 때.
- PRD 파이프라인이 진행 중이 아니어도 독립적으로 실행 가능하다 (PRD가 없어도 된다).
- 전형적인 사용처는 **이 세션의 `backend-implementer`가 만들지 않은 외부 PR**을 리뷰하는 것이다. 이 세션이 직접 구현하고 이미 [3a]/[3b]를 통과시킨 코드라면 굳이 이 스킬을 다시 돌릴 필요는 없다.
- `prd-review`(PRD 자체의 완전성)나 `convention-check`(스타일)와는 다르다 — 이 스킬은 **이미 작성된 코드**의 기능적 정확성/보안/통합 이슈를 본다.

## 원칙 (이 스킬 전용)

1. **팀은 리뷰 1회 실행 단위로 존재한다.** "세션당 한 팀"은 "PR 리뷰 1회 실행당 한 팀"으로 읽는다 — 같은 대화 세션에서 **다른** PR을 리뷰할 때는 이전 팀을 완전히 해체(Teardown)한 뒤 새로 스폰한다. 재사용은 오직 **같은 PR**의 재검토/재검증(FIX 반영 후 재리뷰 등)에만 해당한다.
2. **Phase 2의 피어 수는 항상 정확히 2명**(`pr-security-reviewer`, `pr-integration-tester`)으로 고정한다. 새로운 리뷰 관점(예: 성능)이 필요해지면 Phase 3을 신설하지, Phase 2에 세 번째 피어를 끼워 넣지 않는다.
3. **피어 간 SendMessage는 한 번에 정확히 한 명, 구체적 발견 사항 1건**에 대해서만 보낸다. 양쪽에 동시 전송(브로드캐스트)하지 않고, PASS/FIX/REDO 판정 자체를 피어에게 보내지 않는다 — 판정은 항상 리더행이다.
4. 리더는 스폰 이후 개별 단계를 지시하지 않는다 — 완료 보고를 기다렸다가 통합하는 역할에 집중한다.
5. **리뷰 전용 — 대상 브랜치/diff를 오염시키지 않는다.** 이 스킬은 리뷰만 하고 대상 코드를 바꾸지 않는다. `pr-integration-tester`가 시나리오 재현을 위해 테스트를 쓸 수는 있으나 그것은 일회용 스캐폴딩이며 보고 전에 반드시 제거된다(아래 격리/정리 참고). 리더는 리뷰 종료 전 워킹 트리가 리뷰 시작 시점과 동일한지 확인한다.

## 격리 (권장) 또는 정리 (필수)

PR을 실제로 기동·검증하려면 코드를 체크아웃해야 하고, `pr-integration-tester`는 통합 테스트를 쓸 수 있다. 이 쓰기가 대상 PR 브랜치에 남으면 리뷰 중인 diff가 오염된다. 두 가지로 방지한다:

- **격리 (권장)**: 대상 브랜치를 **일회용 워크트리/임시 체크아웃**에 두고 그 안에서만 리뷰·테스트를 진행한 뒤, 리뷰 종료 시 통째로 폐기한다. 이 저장소의 프로젝트 지시(이 스킬)가 워크트리 사용을 명시하는 것이므로 허용된다. 빌드/기동이 필요한 PR에서 특히 권장한다.
- **정리 (필수 백스톱)**: 격리를 쓰지 않았다면, `pr-integration-tester`는 자신이 만든 테스트 파일을 판정 직후 모두 삭제해 워킹 트리를 baseline으로 되돌린다. 리더는 Teardown에서 `git status --short`가 깨끗한지(잔여물 없음) 반드시 확인하고, 잔여물이 있으면 제거하기 전까지 리뷰를 완료로 보고하지 않는다.

## Phase 1 — 기능 게이트 (`code-verifier` 단독)

1. `TaskCreate`로 "PR 기능 검증 (Phase 1)" 태스크를 만든다. description에 PR diff와 (있다면) PR 설명/연결된 이슈를 담는다.
2. `code-verifier`를 `Agent`로 스폰하며 이 태스크 ID를 전달한다. `code-verifier`의 기본 프롬프트는 PRD 기준이므로, **PRD가 없는 이 맥락에서는 "PR 설명/연결된 이슈/커밋 메시지 + 기존·신규 테스트 통과 여부를 기준으로 판단하라"는 대체 기준을 리더가 스폰 시 반드시 전달한다** (이 지시가 없으면 code-verifier가 존재하지 않는 PRD를 찾게 된다).
3. **FAIL** → Phase 2로 진행하지 않는다. FAIL 사유를 사용자에게 보고하고 종료한다. 이 스킬은 기본적으로 리뷰만 하고 코드를 고치지 않는다 — 사용자가 "고쳐서 다시 리뷰해줘"라고 명시적으로 요청할 때만 별도로 `backend-implementer` 스폰 여부를 사용자와 확인한다.
4. **PASS** → Phase 2로 진행한다.

## Phase 2 — 피어 팀 (`pr-security-reviewer` + `pr-integration-tester`)

1. `TaskCreate`로 "PR 보안 검증 (Phase 2)", "PR 통합 테스트 (Phase 2)" 두 태스크를 만들고, 각각 `TaskUpdate`로 `addBlockedBy`에 Phase 1 태스크 ID를 건다.
2. Phase 1이 PASS로 `completed`된 **뒤에만** 두 에이전트를 `Agent`로 스폰한다. 스폰 메시지는 개별 절차 지시가 아니라 공통 안내로 충분하다: "당신의 태스크는 #N입니다. TaskGet으로 확인하고 in_progress로 바꾸세요. 발견 사항이 상대(피어)의 리뷰 범위에 영향을 준다면 SendMessage로 직접 알리세요 — 판정 자체는 저(리더)에게만 보고하세요."
3. 두 에이전트는 서로 `SendMessage`로 직접 협업한다 — 예: `pr-security-reviewer`가 인가 누락을 발견하면 `pr-integration-tester`에게 "이 엔드포인트에 권한 없는 접근에 대한 회귀 테스트를 추가해달라"고 직접 요청한다. 이 교신은 리더를 거치지 않는다.
4. 리더는 두 태스크를 개별적으로 지시하지 않고 완료 보고를 기다린다. **먼저 도착한 보고를 곧바로 통합 판정으로 취급하지 않는다** — `TaskList`/`TaskGet`으로 두 태스크가 모두 `completed`인지 확인한 뒤에만 통합한다.
5. 아래 표의 상황 외에는 리더가 먼저 말을 걸지 않는다.

### 유휴/에러 개입 기준

| 상황 | 리더의 개입 |
|---|---|
| 태스크가 `in_progress`인 채 리더가 연속 2번 깨어나도 `TaskUpdate`도 SendMessage도 없음 | 해당 팀원에게 상태 확인 메시지 1건 전송. 그래도 조용하면 사용자에게 보고 |
| 두 피어의 판정이 같은 항목에서 서로 모순(예: 한쪽 REDO, 한쪽 PASS) | 리더가 직접 관련 파일/라인을 `Read`로 확인한다. 그래도 불명확하면 양쪽에 **각각**(브로드캐스트 아님) 재검증을 요청한다 |
| 출력 텍스트의 시도 회차와 태스크 metadata가 어긋남 | 태스크 metadata를 신뢰하고 해당 팀원에게 확인을 요청한다 |
| 팀원이 사람만 답할 수 있는 질문을 SendMessage로 보냄 | 그대로 사용자에게 전달하고, 답이 올 때까지 해당 태스크는 열어둔다 — 리더가 대신 답하지 않는다 |
| `pr-integration-tester`의 자기 검증에 잔여 테스트 파일이 남았다고 보고됨 | 리뷰 전용 정리 계약 위반. 잔여물을 제거해 워킹 트리를 baseline으로 되돌리기 전까지 다음 단계로 진행하지 않고, 사용자에게 알린다 |
| `git status --short` 자기 검증에서 그 밖의 "예상치 못한 변경"이 보고됨 | 즉시 사용자에게 알리고 다음 단계로 진행하지 않는다 |

**재시도 루프**: FIX/REDO 판정 시 이 스킬 전용 재시도 카운터를 1 증가시키고, **2회를 초과하면** 태스크 목록 metadata를 근거로 시도 이력을 간결히 정리해(가능하면 `retry-postmortem` 스킬의 절차를 따라) 사용자에게 넘긴다.

## 통합 및 보고

Phase 1 결과 + Phase 2 두 판정(그리고 있었다면 피어 간 교신 요약)을 하나의 리뷰 보고서로 합친다. FIX/REDO가 있으면 어느 파일/라인인지, 무엇을 어떻게 고쳐야 하는지 구체적으로 정리한다 — 각 에이전트의 기존 출력 형식을 그대로 재사용한다.

## 팀 해체 (Teardown)

1. `TaskList`로 Phase 1/2 태스크가 모두 `completed`(또는 에스컬레이션으로 명시적으로 열어둔 상태)인지 확인한다.
2. **워킹 트리 정결성 확인**: `git status --short`로 리뷰 과정에서 생긴 잔여 파일(특히 `pr-integration-tester`의 테스트 스캐폴딩)이 없는지 확인한다. 격리(워크트리)를 썼다면 그 체크아웃을 폐기한다. 잔여물이 있으면 제거해 대상 브랜치/diff를 리뷰 시작 시점과 동일하게 되돌린 뒤에만 완료로 본다.
3. `TaskStop`을 스폰된 팀원 이름별로 호출한다 — `code-verifier`, (Phase 2까지 갔다면) `pr-security-reviewer`, `pr-integration-tester`.
4. 최종 보고에 "팀 해체 완료 + 워킹 트리 정결" 한 줄을 포함한다.
5. 같은 대화 세션에서 **다른** PR을 리뷰하게 되면, 위 해체를 먼저 마친 뒤 새 팀을 처음부터 스폰한다 — 인스턴스를 재사용하지 않는다.

## 출력 형식

```
## PR 리뷰 결과: {PR 식별자}

### Phase 1 — 기능 검증
{PASS / FAIL — 사유}

### Phase 2 — 보안 / 통합 (Phase 1 PASS일 때만)
- 보안: {PASS / FIX(N건) / REDO(N건)}
- 통합: {PASS / FIX(N건) / REDO(N건)}
- 피어 간 교신 요약: {있었다면 무엇을 주고받았는지 한 줄씩}

### 종합 판정
{승인 가능 / 국소 수정 필요 / 재설계 필요 — 근거}

### 팀 해체
TaskStop 완료: {스폰됐던 팀원 이름 목록}
워킹 트리: {정결 — 리뷰 잔여물 없음 / 정리함}
```
