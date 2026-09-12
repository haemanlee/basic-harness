#!/usr/bin/env bash
set -euo pipefail

HARNESS_HOME="${CLAUDE_REVIEW_HOME:-$HOME/.claude-local-review}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK="$REPO_ROOT/.git/hooks/pre-push"
SOURCE="$HARNESS_HOME/scripts/pre-push"

if [ ! -f "$SOURCE" ]; then
  printf 'Missing hook source: %s\n' "$SOURCE" >&2
  exit 1
fi

if [ -f "$HOOK" ]; then
  BACKUP="$HOOK.ai-review-backup.$(date +%Y%m%d_%H%M%S)"
  cp "$HOOK" "$BACKUP"
  printf 'Existing pre-push hook backed up to %s\n' "$BACKUP"
fi

cp "$SOURCE" "$HOOK"
chmod +x "$HOOK"
printf 'Installed ai-review pre-push hook: %s\n' "$HOOK"
printf 'Bypass when intentionally needed: git push --no-verify\n'
