---
name: prd-delta-extractor
description: Extract structured requirements (spec.yaml) and Given/When/Then acceptance criteria from PowerPoint (.pptx) PRDs while only sending CHANGED slides to vision, so token cost scales with the size of the change instead of the size of the deck. Use whenever the PRD/기획서 arrives as .pptx, or the user references a filename ending in .pptx, or colloquially says PPT/피피티/파워포인트/슬라이드/장표/덱(deck) in the same breath as 기획서/PRD/요구사항/스펙 (e.g. "기획서 PPT", "PPT 기획서", "슬라이드 자료", "장표로 된 PRD") — colloquial "PPT"/".ppt" almost always means the modern .pptx format in practice, so treat it as a trigger too; if the actual file turns out to be the legacy binary .ppt, ask the user to save it as .pptx first — or the deck is a re-upload/버전업/개정판 of a previous version, or the user mentions acceptance criteria (AC), 인수조건, requirement drift/요구사항 변경, or comparing PRD versions/버전 비교 — even if they don't say "skill". Runs as a pre-processing step before prd-review's completeness check.
---

# PRD 델타 추출 (PPTX)

이 스킬은 버전이 바뀐 PowerPoint PRD를 diff 가능한 `spec.yaml` + 인수조건(AC)으로 변환한다. `.pptx`는 zip으로 묶인 XML이라 git이 유의미하게 diff할 수 없고, 버전이 바뀔 때마다 전체 덱을 vision으로 다시 읽으면 비용이 덱 크기에 비례해 커진다. 그래서 변경 여부를 로컬에서 먼저 판별하고, **실제로 바뀐 슬라이드만** vision에 태운다.

`prd-review`가 다루는 "PRD 내용이 완전한가"와는 다른 문제를 푼다 — 이 스킬은 "PPTX 포맷에서 구조화된 요구사항을 어떻게 저비용으로 뽑아낼 것인가"를 다룬다. 두 스킬은 순서대로 함께 쓴다: PRD가 `.pptx`면 이 스킬로 먼저 구조화한 뒤, 그 결과(`spec.yaml`/`delta.md`)를 `prd-review` 완전성 체크리스트에 태운다.

## 언제 실행하는가

- PRD/기획서가 `.pptx`로 제공될 때, CLAUDE.md 파이프라인의 [0단계]로 [1단계] `prd-review`보다 **먼저** 실행한다.
- 파일 자체를 첨부하지 않고 말로만 언급해도 트리거한다. 예: "기획서 PPT 보내드릴게요", "PPT로 된 PRD 검토해줘", "슬라이드 자료 리뷰", "장표 기획서", "버전업된 덱 다시 봐줘", "지난 PPT랑 뭐가 달라졌는지". `.pptx`로 끝나는 파일명이 언급되면 확장자만으로도 트리거 대상이다.
- 사용자가 습관적으로 "PPT"라고 부르지만 실제 파일이 구버전 바이너리 `.ppt`(97-2003)인 경우, `detect_changes.py`의 슬라이드 XML 해싱은 OOXML(`.pptx`) 구조를 전제하므로 그대로는 동작하지 않는다 — 이때는 `.pptx`로 다른 이름으로 저장 후 다시 달라고 안내한다.
- 이전 버전 `.pptx`와 `.cache/manifest.json`이 있으면 버전 비교(델타) 모드로 동작한다. 없으면(`first_run: true`) 전체 슬라이드를 1회 처리한다 — 비교 대상이 없으니 당연한 동작이다.
- PRD가 텍스트/마크다운으로 제공되는 일반적인 경우에는 이 스킬을 건너뛰고 곧바로 `prd-review`를 실행한다.

## 원칙

1. 버전이 바뀌었다고 모든 슬라이드를 vision으로 읽지 않는다. 반드시 변경 게이트를 먼저 돌리고, 게이트가 변경으로 보고한 슬라이드만 연다.
2. diff의 기준은 슬라이드 순서가 아니라 `spec.yaml`의 안정적인 `REQ-####` ID다. `spec.yaml`과 `.cache/manifest.json`은 `.pptx` 옆에 커밋한다.
3. 추출은 재현 가능해야 한다 — 같은 `.pptx`를 넣으면 같은 `spec.yaml`이 나와야 하고, 슬라이드가 옮겨졌다고 REQ ID를 다시 매기지 않는다.
4. 인수조건은 스펙 조각이 바뀐 요구사항에 대해서만 재생성한다.

## 절차

### 1. 변경 게이트 (vision 없이, 무료)

```bash
python scripts/detect_changes.py NEW.pptx --cache .cache --out changes.json
```

슬라이드마다 정규화한 슬라이드 XML 해시와 PNG의 perceptual dHash(폴백)를 이전 매니페스트와 비교해 `changes.json`(`changed`/`unchanged`/`png_dir`/`first_run`)을 만든다.

### 2. 변경된 슬라이드만 추출 (vision)

`changed`에 속한 슬라이드 번호마다 `png_dir/slide-<N>.png`를 열어 `SPEC_SCHEMA.md` 형식에 맞는 요구사항 조각으로 추출한다.

- 같은 요구사항이 계속 존재한다고 판단되면 기존 `REQ-####` ID를 재사용하고, 정말 새로운 요구사항일 때만 새 ID를 부여한다.
- `unchanged` 슬라이드는 절대 열지 않는다 — `.cache/manifest.json`의 캐시된 조각을 그대로 재사용한다.
- 캐시된 조각(미변경) + 새로 추출한 조각(변경)을 합쳐 `spec.yaml`을 조립한다.

### 3. 검증

```bash
python scripts/validate_spec.py spec.yaml
```

필수 필드가 빠진 요구사항이 있으면 실패하며 어떤 `REQ-####`의 어떤 필드가 빠졌는지 구체적으로 알려준다. 실패하면 내용을 임의로 지어내지 말고 해당 REQ ID/필드를 짚어 사용자에게 확인한다.

### 4. 이전 버전과 diff

```bash
python scripts/diff_spec.py OLD_spec.yaml spec.yaml --out delta.md
```

요구사항 단위로 추가/삭제/수정(필드별)을 정리한 `delta.md`를 만든다. PR에 그대로 붙여넣을 수 있는 산출물이다.

### 5. 변경된 요구사항만 인수조건 재생성

`diff_spec.py`가 추가/수정으로 표시한 `REQ-####`에 대해서만 `AC_TEMPLATE.md`의 Given/When/Then 형식으로 AC를 작성해 `acceptance_criteria.md`에 반영한다. 미변경 요구사항의 AC는 건드리지 않는다.

### 6. 커밋 대상 안내

`NEW.pptx`, `spec.yaml`, `.cache/manifest.json`, `delta.md`, `acceptance_criteria.md`를 함께 커밋하도록 사용자에게 안내한다 — 다음 버전 비교의 기준이 된다.

## 참고 파일

- `SPEC_SCHEMA.md` — `spec.yaml` 요구사항 항목의 정확한 형식 (추출 전에 읽는다).
- `AC_TEMPLATE.md` — Given/When/Then 형식과 예시 (AC 작성 전에 읽는다).

## 의존성

`libreoffice`(또는 `soffice`)와 `pdftoppm`(렌더링용), Python `Pillow`와 `PyYAML`. `python-pptx`가 있으면 XML 레벨 해싱에 사용한다. 해싱은 순수 Python이라 `imagehash`는 필요 없다. 도구가 없으면 사용자에게 알리고, 전체 덱을 vision으로 대체 처리하지 않는다.

## 출력 형식

```
## PRD 델타 추출 결과: {파일명}

- 처리 모드: {첫 실행 / 버전 비교}
- 슬라이드: 전체 M장 중 변경 N장 → vision 처리 [슬라이드 번호 목록]
- spec.yaml: 요구사항 K건 (신규 A건 / 수정 B건 / 삭제 C건)
- validate_spec.py: {OK / FAIL — 문제 목록}
- 갱신된 산출물: spec.yaml, delta.md, acceptance_criteria.md, .cache/manifest.json

이 산출물(spec.yaml, delta.md)을 prd-review 완전성 검토의 입력으로 전달한다.
```
