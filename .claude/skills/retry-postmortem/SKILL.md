---
name: retry-postmortem
description: Summarizes the retry/rework history into a concise diagnostic report when the pipeline escalates to the user — either after code-verifier's functional loop exceeds 3 retries, or after the security/integration (FIX/REDO) loop exceeds 2 retries. Use only at escalation time, not on every retry. Produces a short attempt-history table plus the core open question, not a raw log dump.
---

# 재작업 이력 요약 (에스컬레이션용)

재시도 한도를 초과해 사용자에게 판단을 넘겨야 할 때, 지금까지의 시도 이력을 사람이 한눈에 파악할 수 있도록 정리한다. 원본 로그나 각 시도의 전체 피드백을 그대로 나열하지 않는다.

## 언제 실행하는가

- [3a] `code-verifier` 재작업 루프가 3회를 초과했을 때
- [3b] `security-reviewer`/`integration-tester` 재작업 루프(FIX/REDO)가 2회를 초과했을 때

## 절차

1. 각 시도에서 무엇을 바꿨는지, 어느 검증 단계에서 왜 막혔는지 나열한다.
2. 매 시도마다 같은 항목에서 반복적으로 막히는 패턴이 있는지 확인한다 (반복 패턴이 있다면 PRD 자체의 모호함이나 구조적 문제일 가능성이 큼).
3. 사람이 판단해야 할 핵심 쟁점을 1~2가지로 압축한다.

## 출력 형식

```
## 재작업 에스컬레이션 요약

### 시도 이력
| 회차 | 시도한 내용 | 막힌 단계 | 판정 |
|---|---|---|---|
| 1 | ... | code-verifier | FAIL |
| 2 | ... | security-reviewer | REDO |
...

### 반복 패턴
{같은 항목에서 계속 막히는지, 매번 다른 문제인지}

### 마지막 피드백
{가장 최근 검증 단계의 피드백 핵심만 요약}

### 사람이 판단해야 할 핵심 쟁점
1. ...
2. ...
```
