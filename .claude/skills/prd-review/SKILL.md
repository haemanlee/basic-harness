---
name: prd-review
description: Review a PRD, 기획서, or feature spec for completeness — missing required sections, edge cases, and exception handling. Use whenever the user asks to review, check, validate, or 검토/리뷰 a PRD, 기획서, requirements document, or feature spec, or mentions completeness/누락 in that context. Outputs an issue list grouped by severity (critical/major/minor).
---

# PRD 완전성 검토

이 스킬은 PRD/기획서의 **완전성(누락 항목)**을 중점적으로 검토한다. 문체나 표현을 다듬는 것이 목적이 아니라, 구현 단계로 넘어가기 전에 빠진 요구사항을 잡아내는 게이트 역할을 한다.

## 검토 절차

1. 대상 문서를 읽고 아래 체크리스트 항목별로 존재 여부를 확인한다.
2. 각 항목이 누락되었거나 모호하면 이슈로 기록한다.
3. 이슈를 심각도별로 분류해 목록으로 출력한다. 서술형 요약이나 인라인 수정 제안은 하지 않는다.

## 완전성 체크리스트

| 구분 | 확인 항목 |
|---|---|
| 목적/배경 | 왜 이 기능이 필요한지, 해결하려는 문제가 명시되어 있는가 |
| 기능 요구사항 | 핵심 기능 흐름(happy path)이 빠짐없이 서술되어 있는가 |
| 예외 케이스 | 실패/오류 상황에 대한 처리 방침이 정의되어 있는가 |
| 엣지 케이스 | 경계값, 동시성, 빈 값/최대값 등 비정상 입력 케이스가 다뤄졌는가 |
| 비기능 요구사항 | 성능, 보안, 인증/인가, 로깅 등 비기능 요건이 언급되어 있는가 |
| 데이터 정의 | 입출력 데이터 구조, 필수/선택 필드가 명확한가 |
| 성공 지표 | 완료 기준(Definition of Done) 또는 성공 지표가 있는가 |
| 이해관계자/의존성 | 연관 시스템, 외부 API, 담당자 등 의존 관계가 명시되어 있는가 |

## 심각도 기준

- **critical**: 이 항목이 없으면 구현을 시작할 수 없거나 잘못된 방향으로 구현될 위험이 큼 (예: 핵심 기능 흐름 누락, 데이터 정의 누락)
- **major**: 구현은 가능하지만 재작업 위험이 있는 누락 (예: 예외 케이스 일부 누락, 성공 지표 불명확)
- **minor**: 구현에 큰 영향은 없지만 보완이 필요한 항목 (예: 이해관계자 정보 누락)

## 출력 형식

```
## PRD 검토 결과: {문서명}

### Critical (N건)
- [항목] 설명 — 왜 문제인지, 어떤 정보가 필요한지

### Major (N건)
- [항목] 설명

### Minor (N건)
- [항목] 설명

### 종합 판정
critical 이슈 {있음/없음} → {구현 진행 가능 / PRD 보완 필요}
```

Critical 이슈가 하나라도 있으면 반드시 "PRD 보완 필요"로 판정한다. 이 판정 결과는 오케스트레이션(CLAUDE.md)에서 다음 단계 진행 여부를 결정하는 데 사용된다.
