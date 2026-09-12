#!/usr/bin/env bash
set -euo pipefail

HARNESS_HOME="${CLAUDE_REVIEW_HOME:-$HOME/.claude-local-review}"
BASE="${CLAUDE_REVIEW_BASE:-origin/main}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$HARNESS_HOME/runs/$REPO_NAME/$RUN_ID"
mkdir -p "$RUN_DIR"
cd "$REPO_ROOT"

"$HARNESS_HOME/scripts/collect-context.sh" "$BASE" > "$RUN_DIR/context.txt"
git diff "$BASE"...HEAD > "$RUN_DIR/diff.patch"
RISK="$("$HARNESS_HOME/scripts/classify-risk.sh" "$BASE")"
printf 'Risk: %s\n' "$RISK"

run_reviewer() {
  local name="$1" model="$2"
  local prompt="$HARNESS_HOME/prompts/reviewer-$name.md"
  local output="$RUN_DIR/$name-review.md"
  { cat "$prompt"; printf '\n\n# Review context\n'; cat "$RUN_DIR/context.txt"; } |
    claude --print --model "$model" > "$output"
  printf '\n=== %s ===\n' "$name"
  cat "$output"
}

run_reviewer backend sonnet
if [ "$RISK" = MEDIUM ] || [ "$RISK" = HIGH ]; then
  run_reviewer production sonnet
fi
if [ "$RISK" = HIGH ]; then
  run_reviewer adversarial opus
fi

printf '\nArtifacts: %s\n' "$RUN_DIR"
