#!/usr/bin/env python3
"""Validate spec.yaml against the required-field rules in SPEC_SCHEMA.md.

Exits non-zero and prints every problem so the model knows exactly which REQ to ask the
user about — instead of silently inventing missing content.

Usage:
    python validate_spec.py spec.yaml
"""
import sys
from pathlib import Path

import yaml

REQUIRED = ["id", "title", "slide", "description", "done_when", "source_hash"]
LIST_FIELDS = ["constraints", "done_when", "open"]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: validate_spec.py spec.yaml")
    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"no such file: {path}")

    data = yaml.safe_load(path.read_text()) or {}
    reqs = data.get("requirements")
    problems = []

    if not isinstance(reqs, list) or not reqs:
        sys.exit("spec.yaml has no 'requirements:' list")

    seen_ids = set()
    for i, r in enumerate(reqs):
        tag = r.get("id", f"<item #{i}>")
        for f in REQUIRED:
            if f not in r or r[f] in (None, "", []):
                problems.append(f"{tag}: missing required field '{f}'")
        if "id" in r:
            if r["id"] in seen_ids:
                problems.append(f"{tag}: duplicate id")
            seen_ids.add(r["id"])
            if not str(r["id"]).startswith("REQ-"):
                problems.append(f"{tag}: id must look like REQ-####")
        for f in LIST_FIELDS:
            if f in r and r[f] is not None and not isinstance(r[f], list):
                problems.append(f"{tag}: field '{f}' must be a list")
        dw = r.get("done_when")
        if isinstance(dw, list):
            for item in dw:
                if isinstance(item, str) and len(item.strip()) < 8:
                    problems.append(f"{tag}: done_when item too vague: '{item}'")

    if problems:
        print(f"FAIL — {len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print(f"OK — {len(reqs)} requirements, all required fields present.")


if __name__ == "__main__":
    main()
