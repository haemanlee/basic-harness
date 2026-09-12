#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-origin/main}"
FILES="$(git diff --name-only "$BASE"...HEAD)"
LINES="$(git diff --numstat "$BASE"...HEAD | awk '{a+=$1; d+=$2} END {print a+d+0}')"
DIFF="$(git diff "$BASE"...HEAD)"
RISK=LOW

if printf '%s\n' "$FILES" | grep -Eiq 'reward/|payment/|withdrawal/|settlement/|auth/|security/|migration/'; then
  RISK=HIGH
elif printf '%s\n' "$DIFF" | grep -Eiq '@Transactional|retry|idempotency|SELECT FOR UPDATE'; then
  RISK=HIGH
elif [ "$LINES" -gt 500 ]; then
  RISK=HIGH
elif [ "$LINES" -gt 150 ]; then
  RISK=MEDIUM
fi

printf '%s\n' "$RISK"
