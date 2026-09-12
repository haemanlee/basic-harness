# Claude Code Local Review Harness v0.1

A personal pre-MR review harness for Claude Code. Install it into `~/.claude-local-review` and use it from any Git repository without adding review artifacts or configuration to that repository.

## Design

- Global local harness = HOW to review: personas, execution, model routing.
- Repository-local override (future) = WHAT is risky in that repository.
- Start from the Git diff; avoid broad repository exploration.
- LOW risk: backend reviewer (Sonnet).
- MEDIUM risk: backend + production reviewers (Sonnet).
- HIGH risk: backend + production (Sonnet) + adversarial (Opus).
- Runs are stored outside repositories under `~/.claude-local-review/runs/<repo>/<timestamp>`.

## Install

```bash
git clone https://github.com/haemanlee/basic-harness.git
cd basic-harness/local-review
./install.sh
alias ai-review="$HOME/.claude-local-review/scripts/ai-review.sh"
```

Requires `git` and an authenticated Claude Code `claude` CLI.

## Run

From a feature branch:

```bash
git fetch origin main
ai-review
```

Override the comparison base when needed:

```bash
CLAUDE_REVIEW_BASE=origin/develop ai-review
```

## Output

Review artifacts are written only to the local home directory:

```text
~/.claude-local-review/runs/<repo>/<timestamp>/
  diff.patch
  context.txt
  backend-review.md
  production-review.md   # MEDIUM/HIGH only
  adversarial-review.md  # HIGH only
```

## Repository-specific rules (next iteration)

For private local overrides without changing Git-tracked files, create `.repo-local-review.yaml` and add it to the repository's `.git/info/exclude`. v0.1 intentionally keeps this out of the execution path until the core workflow has been evaluated.

## Evaluation before team adoption

Use this personally for roughly two weeks and record: actionable P0/P1 findings, false positives, review latency/token usage, and defects caught before MR. Promote it into a team repository only after the workflow demonstrates value.
