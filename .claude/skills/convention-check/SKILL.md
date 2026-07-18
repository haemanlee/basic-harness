---
name: convention-check
description: Advisory, non-blocking check of Java/Kotlin (Spring) code style, layer separation (Controller/Service/Repository), and naming conventions — areas code-verifier intentionally does not cover. Use once, after all functional/security/integration gates have passed, as part of pipeline wrap-up. Findings are informational only and never block the pipeline.
---

# 코드 컨벤션 점검

이 스킬은 `code-verifier`, `security-reviewer`, `integration-tester`가 다루지 않는 **스타일·컨벤션** 영역을 가볍게 점검한다. 다른 검증 단계와 달리 이 스킬의 결과는 파이프라인을 막지 않는다 — 최종 완료 보고서에 참고 항목으로만 첨부된다.

## 언제 실행하는가

- [3a] 기능 검증과 [3b] 보안/통합 검증이 모두 PASS로 끝난 뒤, 마무리 단계에서 **한 번만** 실행한다.
- 재작업 루프가 도는 중에는 실행하지 않는다 (비용 절감 — 최종 산출물에 대해서만 확인하면 충분하다).

## 점검 항목

| 구분 | 확인 내용 |
|---|---|
| 레이어 분리 | Controller가 비즈니스 로직을 직접 갖고 있지 않은가, Repository 접근이 Service를 거치는가 |
| 네이밍 | 클래스/메서드/변수명이 프로젝트 관례(또는 표준 Spring 관례)를 따르는가 |
| 의존성 주입 | 생성자 주입을 사용하는가, 필드 주입이 남아있지 않은가 |
| 예외 처리 스타일 | 예외를 삼키지 않고 일관된 방식(예: `@ControllerAdvice`)으로 처리하는가 |
| DTO/Entity 분리 | 외부 응답에 Entity를 그대로 노출하지 않는가 |

## 출력 형식

```
## 컨벤션 점검 결과 (참고용, 비차단)

- [항목] 확인됨 / 개선 여지 있음 — 설명
...

이 항목들은 파이프라인을 막지 않습니다. 필요 시 별도로 개선해주세요.
```
