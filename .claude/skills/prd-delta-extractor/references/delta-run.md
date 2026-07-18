# 버전 비교 절차 (first_run: false)

`changes.json`의 `first_run`이 `false`일 때만 이 문서를 연다 — `.cache/manifest.json`에 이전 버전 기록이 있는, 이 스킬의 본래 목적인 "델타 추출" 절차다.

## 절차

1. `changed` 슬라이드만 vision으로 연다. `unchanged`는 절대 열지 않고 `.cache/manifest.json`의 캐시된 spec 조각을 그대로 재사용한다. (`changed`가 8장을 넘으면 `batch-extraction.md`도 함께 적용한다.)
2. 각 변경 슬라이드를 추출할 때 `SPEC_SCHEMA.md`를 함께 연다:
   - 같은 요구사항이 여전히 존재한다고 판단되면 기존 `REQ-####`를 재사용한다 (제목/설명 문구가 바뀌어도 핵심 의도가 같으면 재사용).
   - 정말 새로운 요구사항일 때만 새 ID(기존 최대값 + 1)를 부여한다.
3. 캐시 조각(미변경) + 새 추출 조각(변경)을 합쳐 `spec.yaml`을 조립하고 `python scripts/validate_spec.py spec.yaml`로 검증한다. 실패하면 `validation-failures.md`를 연다.
4. `python scripts/diff_spec.py OLD_spec.yaml spec.yaml --out delta.md`로 이전 버전과 diff한다.
5. `diff_spec.py`가 added/modified로 표시한 `REQ-####`에 대해서만 `AC_TEMPLATE.md` 형식으로 AC를 재생성한다. 나머지 요구사항의 AC는 건드리지 않는다.
6. 사용자에게 `NEW.pptx`, `spec.yaml`, `.cache/manifest.json`, `delta.md`, `acceptance_criteria.md`를 함께 커밋하라고 안내한다 — 다음 버전 비교의 기준이 된다.
