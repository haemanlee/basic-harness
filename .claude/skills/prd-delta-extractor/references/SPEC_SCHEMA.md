# Spec schema (`spec.yaml`)

`spec.yaml` is the diffable source of truth extracted from the PRD deck. It is a list
of requirements under a top-level `requirements:` key. Keep keys in the order below so
diffs stay clean.

## Requirement fields

| Field         | Required | Notes |
|---------------|----------|-------|
| `id`          | yes      | `REQ-####`, stable across versions. Never renumber on slide move. |
| `title`       | yes      | One line, imperative. |
| `slide`       | yes      | Source slide number in the current deck (provenance only, NOT the diff key). |
| `description` | yes      | What the requirement is, in full sentences. Rewrite slide fragments into prose. |
| `rationale`   | no       | Why it exists, if the slide states it. Omit if unknown; do not invent. |
| `constraints` | no       | List of hard limits (perf, security, platform, dependency). |
| `done_when`   | yes      | List of testable completion conditions. Each item must be verifiable, not vague. |
| `open`        | no       | List of unresolved questions found on the slide. |
| `source_hash` | yes      | Hash of the slide the fragment came from; written by tooling, used for caching. |

## ID stability rule

When re-extracting a changed slide, reuse the existing `id` if the requirement is
recognizably the same thing (same core intent), even if wording changed. Mint a fresh
`REQ-####` (max existing + 1) only for a genuinely new requirement. This is what lets
`diff_spec.py` report "REQ-0014 modified" instead of "everything changed".

## Example

```yaml
requirements:
  - id: REQ-0014
    title: Rate-limit password reset requests
    slide: 7
    description: >-
      The password reset endpoint must throttle requests per account to prevent
      enumeration and abuse.
    rationale: Security review flagged unlimited reset attempts in v3.
    constraints:
      - Max 5 reset requests per account per hour
      - Applies per account, not per IP
    done_when:
      - A 6th reset request within one hour returns HTTP 429
      - The limit is enforced per account regardless of source IP
      - Rejected attempts are logged with account id and timestamp
    open:
      - Should the window be rolling or fixed?
    source_hash: "a1b2c3d4"
```

## Writing rules

- `done_when` items must be things a QA engineer could check. "Fast" is not a
  completion condition; "p95 latency < 200ms under 100 rps" is.
- Turn bullet fragments from the slide into complete, unambiguous sentences.
- If a slide is a title/section divider with no requirement, produce no requirement for
  it (record nothing rather than a placeholder).
