# 첫 실행 절차 (first_run: true)

`changes.json`의 `first_run`이 `true`일 때만 이 문서를 연다 — `.cache/manifest.json`이 없어 비교할 이전 버전이 없는 경우다. 델타 규칙(ID 재사용, diff, "변경분만" AC)이 필요 없는 별도 절차이므로 `delta-run.md`와 분리되어 있다.

## 절차

1. `changed` 목록은 전체 슬라이드 번호와 같다. 전체를 vision으로 연다. (슬라이드가 8장을 넘으면 `batch-extraction.md`도 함께 적용한다.)
2. 슬라이드마다 `SPEC_SCHEMA.md` 형식에 맞춰 새 `REQ-####`를 순서대로 발급한다(`REQ-0001`부터). 재사용할 기존 ID가 없다.
3. `spec.yaml`을 조립한 뒤 `python scripts/validate_spec.py spec.yaml`로 검증한다. 실패하면 `validation-failures.md`를 연다.
4. **`diff_spec.py`는 실행하지 않는다** — 비교할 이전 버전이 없다. `delta.md`도 만들지 않는다.
5. 모든 요구사항에 대해 `AC_TEMPLATE.md` 형식으로 AC를 작성한다 — "변경분만"이 아니라 전부 새 것이므로 전체 작성한다.
6. 사용자에게 `NEW.pptx`, `spec.yaml`, `.cache/manifest.json`, `acceptance_criteria.md`를 함께 커밋하라고 안내한다 (`delta.md`는 없음 — 다음 버전 비교부터 생성된다).
