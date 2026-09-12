#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-origin/main}"

echo '# Changed files'
git diff --name-only "$BASE"...HEAD
echo
echo '# Diff'
git diff "$BASE"...HEAD
