#!/usr/bin/env bash
set -euo pipefail

HARNESS_HOME="${CLAUDE_REVIEW_HOME:-$HOME/.claude-local-review}"
BASE="${CLAUDE_REVIEW_BASE:-origin/main}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$HARNESS_HOME/runs/$REPO_NAME/$RUN_ID"
STATE_DIR="$HARNESS_HOME/state/$REPO_NAME"
STATE_FILE="$STATE_DIR/last-review.env"
mkdir -p "$RUN_DIR" "$STATE_DIR"
cd "$REPO_ROOT"

"$HARNESS_HOME/scripts/collect-context.sh" "$BASE" > "$RUN_DIR/context.txt"
git diff "$BASE"...HEAD > "$RUN_DIR/diff.patch"
RISK="$("$HARNESS_HOME/scripts/classify-risk.sh" "$BASE")"
printf 'Risk: %s\n' "$RISK"

RESULT=PASS

run_reviewer() {
  local name="$1" model="$2"
  local prompt="$HARNESS_HOME/prompts/reviewer-$name.md"
  local output="$RUN_DIR/$name-review.md"
  { cat "$prompt"; printf '\n\n# Review context\n'; cat "$RUN_DIR/context.txt"; } |
    claude --print --model "$model" > "$output"
  printf '\n=== %s ===\n' "$name"
  cat "$output"

  if grep -Eq '^\[P[01]\]|(^|[^A-Z])P[01]([^0-9]|$)' "$output"; then
    RESULT=BLOCK
  elif grep -Eq '^\[P2\]|(^|[^A-Z])P2([^0-9]|$)' "$output" && [ "$RESULT" = PASS ]; then
    RESULT=WARN
  fi
}

run_reviewer backend sonnet
if [ "$RISK" = MEDIUM ] || [ "$RISK" = HIGH ]; then
  run_reviewer production sonnet
fi
if [ "$RISK" = HIGH ]; then
  run_reviewer adversarial opus
fi

REVIEWED_HEAD_SHA="$(git rev-parse HEAD)"
printf 'REVIEWED_HEAD_SHA=%q\n' "$REVIEWED_HEAD_SHA" > "$STATE_FILE"
printf 'RESULT=%q\n' "$RESULT" >> "$STATE_FILE"
printf 'RISK=%q\n' "$RISK" >> "$STATE_FILE"
printf 'RUN_DIR=%q\n' "$RUN_DIR" >> "$STATE_FILE"
printf 'REVIEWED_AT=%q\n' "$(date -Iseconds)" >> "$STATE_FILE"

printf '\nReview result: %s\n' "$RESULT"
printf 'Artifacts: %s\n' "$RUN_DIR"

if [ "$RESULT" = BLOCK ]; then
  exit 2
fi
