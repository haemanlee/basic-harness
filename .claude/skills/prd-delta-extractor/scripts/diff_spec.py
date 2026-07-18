#!/usr/bin/env python3
"""Diff two spec.yaml versions by REQ-ID and emit a PR-ready Markdown report.

Diffing is keyed on `id`, never on slide order, so a reshuffled deck shows up as
"REQ-0014 modified" rather than a wall of noise.

Usage:
    python diff_spec.py OLD_spec.yaml NEW_spec.yaml --out delta.md
"""
import argparse
from pathlib import Path

import yaml

# Fields compared for "modified"; provenance-only fields are ignored so a slide move
# doesn't count as a content change.
COMPARE = ["title", "description", "rationale", "constraints", "done_when", "open"]


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text()) or {}
    return {r["id"]: r for r in data.get("requirements", []) if "id" in r}


def field_diff(old: dict, new: dict) -> list[str]:
    lines = []
    for f in COMPARE:
        o, n = old.get(f), new.get(f)
        if o != n:
            lines.append(f"  - **{f}**")
            lines.append(f"    - old: {o!r}")
            lines.append(f"    - new: {n!r}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--out", type=Path, default=Path("delta.md"))
    args = ap.parse_args()

    old = load(args.old)
    new = load(args.new)
    old_ids, new_ids = set(old), set(new)

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    modified = sorted(
        i for i in (old_ids & new_ids)
        if any(old[i].get(f) != new[i].get(f) for f in COMPARE)
    )

    out = ["# PRD spec delta", ""]
    out.append(f"- Added: {len(added)}  |  Removed: {len(removed)}  |  "
               f"Modified: {len(modified)}")
    out.append("")

    if added:
        out.append("## Added")
        for i in added:
            out.append(f"- **{i}** — {new[i].get('title','')}")
        out.append("")
    if removed:
        out.append("## Removed")
        for i in removed:
            out.append(f"- **{i}** — {old[i].get('title','')}")
        out.append("")
    if modified:
        out.append("## Modified")
        for i in modified:
            out.append(f"### {i} — {new[i].get('title','')}")
            out.extend(field_diff(old[i], new[i]))
            out.append("")
    if not (added or removed or modified):
        out.append("_No requirement-level changes._")

    args.out.write_text("\n".join(out) + "\n")
    print(f"added={len(added)} removed={len(removed)} modified={len(modified)} "
          f"-> {args.out}")
    if added or modified:
        print("regenerate AC for: " + ", ".join(added + modified))


if __name__ == "__main__":
    main()
