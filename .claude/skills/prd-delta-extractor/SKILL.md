---
name: prd-delta-extractor
description: Extract structured requirements (spec.yaml) and Given/When/Then acceptance criteria from PowerPoint (.pptx) PRDs while only sending CHANGED slides to vision, so token cost scales with the size of the change instead of the size of the deck. Use whenever the PRD/기획서 arrives as .pptx, or the user references a filename ending in .pptx, or colloquially says PPT/피피티/파워포인트/슬라이드/장표/덱(deck) in the same breath as 기획서/PRD/요구사항/스펙 (e.g. "기획서 PPT", "PPT 기획서", "슬라이드 자료", "장표로 된 PRD") — colloquial "PPT"/".ppt" almost always means the modern .pptx format in practice, so treat it as a trigger too; if the actual file turns out to be the legacy binary .ppt, ask the user to save it as .pptx first — or the deck is a re-upload/버전업/개정판 of a previous version, or the user mentions acceptance criteria (AC), 인수조건, requirement drift/요구사항 변경, or comparing PRD versions/버전 비교 — even if they don't say "skill". Runs as a pre-processing step before prd-review's completeness check.
---

# PRD 델타 추출 (PPTX) — 라우터

이 파일은 얇은 라우터다. **항상 필요한 최소 정보만** 여기 담고, 단계별 상세 절차는 `references/`에 나눠 두어 **해당 신호가 실제로 발생했을 때만** 연다. 매 실행마다 전체 워크플로우 문서를 다 읽지 않는 것이 이 스킬 자체의 설계 목적(토큰 절약)과 일치한다.

`.pptx`는 zip으로 묶인 XML이라 git이 유의미하게 diff할 수 없고, 버전마다 전체 덱을 vision으로 다시 읽으면 비용이 덱 크기에 비례해 커진다. 그래서 변경 여부를 로컬에서 먼저 판별하고, 실제로 바뀐 슬라이드만 vision에 태운다. `prd-review`가 다루는 "PRD 내용이 완전한가"와는 다른 문제(PPTX 포맷에서 구조화된 요구사항을 저비용으로 뽑는 것)를 풀며, PRD가 `.pptx`면 이 스킬로 먼저 구조화한 뒤 그 결과(`spec.yaml`/`delta.md`)를 `prd-review` 완전성 체크리스트에 태운다.

## 언제 실행하는가

- PRD/기획서가 `.pptx`로 제공될 때, CLAUDE.md 파이프라인의 [0단계]로 [1단계] `prd-review`보다 **먼저** 실행한다.
- 파일 자체를 첨부하지 않고 말로만 언급해도 트리거한다. 예: "기획서 PPT 보내드릴게요", "PPT로 된 PRD 검토해줘", "슬라이드 자료 리뷰", "장표 기획서", "버전업된 덱 다시 봐줘", "지난 PPT랑 뭐가 달라졌는지". `.pptx`로 끝나는 파일명 언급만으로도 트리거 대상이다.
- 사용자가 습관적으로 "PPT"라 부르지만 실제 파일이 구버전 바이너리 `.ppt`(97-2003)이면, 아래 게이트 스크립트는 OOXML(`.pptx`) 구조를 전제하므로 그대로는 동작하지 않는다 — `.pptx`로 다시 저장해달라고 안내한다.
- PRD가 텍스트/마크다운으로 제공되는 일반적인 경우에는 이 스킬을 건너뛰고 곧바로 `prd-review`를 실행한다.

## 원칙 (항상 적용)

1. 버전이 바뀌었다고 모든 슬라이드를 vision으로 읽지 않는다 — 반드시 변경 게이트를 먼저 돌린다.
2. diff의 기준은 슬라이드 순서가 아니라 `spec.yaml`의 안정적인 `REQ-####` ID다.
3. 추출은 재현 가능해야 한다 — 같은 `.pptx`를 넣으면 같은 `spec.yaml`이 나와야 한다.
4. 실패나 누락을 만나면 지어내지 말고 사용자에게 구체적으로 묻는다 (어떤 REQ, 어떤 필드인지).

## 절차 — 진입점만 실행하고, 나머지는 아래 라우팅 표를 따른다

**항상 실행 (vision 없이, 무료):**

```bash
python scripts/detect_changes.py NEW.pptx --cache .cache --out changes.json
```

이 결과(`changes.json`)를 읽고, 아래 표에서 조건에 맞는 신호가 있을 때만 해당 참고 파일을 연다.

## 라우팅 표

| 신호 유형 | 조건 | 여는 파일 | 조건부인 이유 |
|---|---|---|---|
| 도메인 분기 신호 | `changes.json`의 `first_run: true` | `references/first-run.md` | 비교 대상이 없는 첫 처리 — ID 재사용/diff 규칙 자체가 무의미 |
| 도메인 분기 신호 | `changes.json`의 `first_run: false` | `references/delta-run.md` | 버전 비교 절차 — ID 재사용, diff, "변경분만 AC" 규칙이 필요 |
| 크기 신호 | `changed` 슬라이드 수 > 8 | `references/batch-extraction.md` | 소규모 델타는 위 두 문서만으로 충분 — 배치 전략은 슬라이드가 많을 때만 의미 있음 |
| 조건부 상세 신호 | 슬라이드 추출(vision) 작업에 진입할 때 | `references/SPEC_SCHEMA.md` | 추출 형식은 실제로 추출할 때만 필요, 게이트 단계에서는 불필요 |
| 조건부 상세 신호 | 작성할 AC가 1건 이상 있을 때 (added/modified) | `references/AC_TEMPLATE.md` | AC를 쓸 대상이 없으면(모두 unchanged) 템플릿을 읽을 이유가 없음 |
| 조건부 상세 신호 | `validate_spec.py`가 실패(FAIL)로 종료할 때 | `references/validation-failures.md` | 검증이 통과하면 트러블슈팅 절차 자체가 불필요 |

표에 없는 조건이 성립하기 전까지는 해당 참고 파일을 열지 않는다.

## 의존성

`libreoffice`(또는 `soffice`)와 `pdftoppm`(렌더링용), Python `Pillow`와 `PyYAML`. `python-pptx`가 있으면 XML 레벨 해싱에 사용한다. 도구가 없으면 사용자에게 알리고, 전체 덱을 vision으로 대체 처리하지 않는다.

## 출력 형식

```
## PRD 델타 추출 결과: {파일명}

- 처리 모드: {첫 실행 / 버전 비교}
- 슬라이드: 전체 M장 중 변경 N장 → vision 처리 [슬라이드 번호 목록]
- spec.yaml: 요구사항 K건 (신규 A건 / 수정 B건 / 삭제 C건)
- validate_spec.py: {OK / FAIL — 문제 목록}
- 갱신된 산출물: spec.yaml, (delta.md,) acceptance_criteria.md, .cache/manifest.json

이 산출물(spec.yaml, delta.md)을 prd-review 완전성 검토의 입력으로 전달한다.
```
