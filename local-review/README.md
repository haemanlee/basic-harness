# Claude Code 로컬 리뷰 하네스 v0.1

Claude Code를 활용해 MR을 올리기 전에 개인 로컬 환경에서 코드 리뷰를 수행하기 위한 하네스입니다. `~/.claude-local-review`에 설치하며, 실제 작업 중인 Git 레포지토리에는 리뷰용 파일이나 설정을 추가하지 않고 사용할 수 있습니다.

## 설계 원칙

- 글로벌 로컬 하네스 = **어떻게 리뷰할 것인가(HOW)**: 리뷰어 페르소나, 실행 방식, 모델 라우팅을 관리합니다.
- 레포지토리별 로컬 오버라이드(향후) = **이 레포에서 무엇이 위험한가(WHAT)**: 서비스별 위험 규칙만 관리합니다.
- 전체 레포지토리를 무작정 탐색하지 않고 Git diff에서 리뷰를 시작합니다.
- LOW 위험: Backend Reviewer (Sonnet)
- MEDIUM 위험: Backend + Production Reviewer (Sonnet)
- HIGH 위험: Backend + Production Reviewer (Sonnet) + Adversarial Reviewer (Opus)
- 실행 결과는 작업 레포 밖의 `~/.claude-local-review/runs/<repo>/<timestamp>`에 저장합니다.

## 설치

```bash
git clone https://github.com/haemanlee/basic-harness.git
cd basic-harness/local-review
./install.sh
alias ai-review="$HOME/.claude-local-review/scripts/ai-review.sh"
```

`git`과 인증이 완료된 Claude Code `claude` CLI가 필요합니다.

## 실행

feature branch에서 다음과 같이 실행합니다.

```bash
git fetch origin main
ai-review
```

비교 대상 브랜치가 `main`이 아닌 경우 다음과 같이 변경할 수 있습니다.

```bash
CLAUDE_REVIEW_BASE=origin/develop ai-review
```

## 리뷰 흐름

```text
구현 완료
  ↓
git diff 수집
  ↓
위험도 분류
  ├─ LOW    → Backend Reviewer
  ├─ MEDIUM → Backend + Production Reviewer
  └─ HIGH   → Backend + Production + Adversarial Reviewer
  ↓
리뷰 결과 확인
  ↓
필요한 코드 수정 및 검증
  ↓
MR 생성
```

위험도 분류 자체에는 LLM을 사용하지 않고 변경 경로, diff 크기, 위험 키워드 등을 이용한 deterministic rule을 사용합니다. 단순 라우팅에 불필요한 토큰을 사용하지 않기 위한 설계입니다.

## 리뷰어 역할

### Backend Reviewer

일반적인 백엔드 코드의 정확성을 중심으로 확인합니다.

- 로직 오류
- Transaction boundary
- 동시성 및 race condition
- idempotency
- 예외 처리
- API contract 변경
- DB consistency

### Production Reviewer

코드가 실제 운영 환경에서 실패할 수 있는 상황을 중심으로 확인합니다.

- timeout / retry
- 외부 API 장애
- DB / Redis 부하
- partial failure
- rollback
- resource exhaustion
- observability
- 배포 및 rollback 위험

### Adversarial Reviewer

정상적인 상황보다 실제 장애를 발생시킬 수 있는 edge case를 공격적으로 찾습니다.

- duplicate execution
- race condition
- stale state
- 잘못된 외부 입력
- message redelivery
- out-of-order event
- partial transaction failure
- authorization / trust boundary 문제

단순히 문제를 많이 나열하는 것이 아니라 **구체적인 failure scenario를 구성할 수 있는 경우에만 finding을 남기도록 제한**합니다.

## 결과 저장 위치

리뷰 결과는 작업 중인 Git 레포지토리에 저장하지 않고 개인 홈 디렉터리에만 저장합니다.

```text
~/.claude-local-review/runs/<repo>/<timestamp>/
  diff.patch
  context.txt
  backend-review.md
  production-review.md   # MEDIUM/HIGH인 경우
  adversarial-review.md  # HIGH인 경우
```

따라서 대상 레포지토리에서 `git status`를 실행해도 리뷰 하네스 실행으로 인한 파일 변경이 발생하지 않습니다.

## 레포지토리별 규칙 (다음 단계)

서비스마다 위험한 영역이 다르기 때문에 향후 `.repo-local-review.yaml`을 통해 레포별 규칙을 오버라이드할 수 있도록 확장할 예정입니다.

예를 들어 reward 서비스에서는 다음과 같은 규칙을 둘 수 있습니다.

```yaml
risk:
  high_paths:
    - reward/
    - settlement/

rules:
  - reward execution must be idempotent
  - retry must never cause duplicate payment
```

이 파일은 팀 레포지토리에 바로 추가하지 않고 `.git/info/exclude`에 등록하여 개인 로컬에서만 사용하는 방향을 권장합니다.

```text
.repo-local-review.yaml
```

즉 기본적인 역할 분리는 다음과 같습니다.

```text
GLOBAL
= HOW to review

REPO LOCAL
= WHAT is risky here
```

## 팀 적용 전 검증

v0.1 단계에서는 CI나 merge gate로 사용하지 않습니다.

우선 개인적으로 약 2주 정도 사용하면서 다음 항목을 확인하는 것을 권장합니다.

- 실제로 유효했던 P0/P1 finding 수
- false positive 비율
- 사람이 MR 리뷰 전에 발견하지 못했을 가능성이 높은 버그
- 리뷰 수행 시간
- 토큰 사용량
- LOW / MEDIUM / HIGH 라우팅이 적절했는지

실제 효과가 확인된 이후에만 팀 레포지토리의 `.claude/` 설정이나 공용 스크립트로 승격하는 것을 목표로 합니다.

초기 목표는 AI 리뷰를 강제하는 것이 아니라 **개발자가 MR을 올리기 전에 저비용으로 독립적인 리뷰 관점을 추가하는 것**입니다.
