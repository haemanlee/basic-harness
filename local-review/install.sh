#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${CLAUDE_REVIEW_HOME:-$HOME/.claude-local-review}"
mkdir -p "$TARGET/prompts" "$TARGET/scripts" "$TARGET/runs" "$TARGET/state"
cp "$SOURCE_DIR/config.yaml" "$TARGET/config.yaml"
cp "$SOURCE_DIR"/prompts/*.md "$TARGET/prompts/"
cp "$SOURCE_DIR"/scripts/* "$TARGET/scripts/"
chmod +x "$TARGET"/scripts/*

printf 'Installed Claude local review harness to %s\n' "$TARGET"
printf 'Optional alias: alias ai-review="%s/scripts/ai-review.sh"\n' "$TARGET"
printf 'To enable the local pre-push guard in a target repository, run:\n'
printf '  %s/scripts/install-pre-push.sh\n' "$TARGET"
printf 'For repo-only overrides later, add .repo-local-review.yaml to .git/info/exclude.\n'
