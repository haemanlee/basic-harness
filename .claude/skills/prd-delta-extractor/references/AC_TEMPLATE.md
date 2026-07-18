# Acceptance criteria format

Write AC in Given/When/Then form, one block per requirement, tagged with the `REQ-####`
so it traces back to the spec. Each scenario must be independently testable. Prefer
several small scenarios over one big one.

## Structure

```markdown
### REQ-#### — <title>

**Scenario: <short name>**
- Given <initial state / preconditions>
- When <action / event>
- Then <observable, checkable outcome>

**Scenario: <another name>**
- Given ...
- When ...
- Then ...
```

Cover the happy path AND the boundary/failure cases the requirement's `constraints` and
`done_when` imply. A constraint like "max 5 per hour" needs both a "5th succeeds" and a
"6th is rejected" scenario.

## Worked example (turning a vague slide into testable AC)

The slide said, roughly: *"Limit password resets so people can't spam them."* That is
not testable as written. Using REQ-0014 from the spec:

**Example — Input requirement:**
```yaml
id: REQ-0014
title: Rate-limit password reset requests
constraints: [Max 5 reset requests per account per hour, Applies per account not per IP]
done_when:
  - A 6th reset request within one hour returns HTTP 429
  - The limit is enforced per account regardless of source IP
```

**Example — Output AC:**
```markdown
### REQ-0014 — Rate-limit password reset requests

**Scenario: Within the allowed rate**
- Given an account that has made 4 reset requests in the past hour
- When the account makes a 5th reset request
- Then the request succeeds and a reset email is sent

**Scenario: Exceeding the rate**
- Given an account that has made 5 reset requests in the past hour
- When the account makes a 6th reset request within that hour
- Then the API responds with HTTP 429 and no email is sent

**Scenario: Limit is per account, not per IP**
- Given two accounts each at 5 requests in the past hour, sharing one source IP
- When a 6th request arrives for account A from that IP
- Then account A is rejected with 429 while account B is unaffected
```

## Rules

- One AC block per requirement; never merge two requirements into one block.
- Every `done_when` entry in the spec must map to at least one Then clause.
- Then clauses must be observable (status codes, log entries, DB state, UI text) — not
  internal feelings like "is fast" or "is secure".
- Only (re)write AC for requirements the diff marks added or modified. Leave the rest.
