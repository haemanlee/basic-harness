---
name: prd-delta-extractor
description: >-
  Extract structured requirements and acceptance criteria from PowerPoint (.pptx)
  PRDs while only sending CHANGED slides to vision, so token cost scales with the
  size of the change instead of the size of the deck. Use this skill whenever the
  user has a .pptx PRD/spec, mentions acceptance criteria (AC), requirement drift,
  comparing PRD versions, a re-uploaded/version-bumped deck, or complains that
  re-processing the whole deck is too expensive — even if they don't say "skill".
---

# PRD Delta Extractor

Turn a version-bumped PowerPoint PRD into a diffable spec plus acceptance criteria,
touching vision only on the slides that actually changed.

## Why this exists (read once, then follow the rules)

A `.pptx` is a zip of XML, so git cannot diff it usefully and re-reading every slide
through vision on each version bump is what burns tokens. The fix is to keep the
`.pptx` as the human-facing view and treat an extracted, ID-stable `spec.yaml` as the
source of truth. Rendering slides to PNG is free (CPU only); tokens are spent **only**
when a PNG is sent to vision. So detect changes locally first, then look at changed
slides only.

## Golden rules

1. NEVER read every slide through vision on a version bump. Run the change gate first
   and open only the slides it reports as changed.
2. The diffable source of truth is `spec.yaml`, keyed by stable `REQ-####` IDs — not
   slide order. Commit `spec.yaml` and `.cache/manifest.json` next to the `.pptx`.
3. Extraction must be reproducible: identical `.pptx` in → identical `spec.yaml` out.
   Preserve REQ IDs across versions; never renumber a requirement just because a slide
   moved.
4. Regenerate acceptance criteria only for requirements whose spec fragment changed.

## Workflow

Run the steps in order. Do not skip the gate.

### 1. Render + gate (free, no vision)

```bash
python scripts/detect_changes.py NEW.pptx --cache .cache --out changes.json
```

This renders each slide to PNG, hashes it two ways (normalized slide XML, then a
perceptual dHash of the PNG as a fallback), compares against `.cache/manifest.json`
from the previous version, and writes `changes.json`:

```json
{
  "changed":  [3, 7],        // 1-based slide numbers needing vision
  "unchanged":[1,2,4,5,6],   // reuse cached spec fragments
  "png_dir":  ".cache/png",
  "first_run": false
}
```

On the very first run everything is "changed" (there is nothing to compare to) and
`first_run` is true — that is expected.

### 2. Extract changed slides only (vision)

For each slide number in `changed`, open `png_dir/slide-<N>.png` and extract its
requirements into fragments that match `SPEC_SCHEMA.md`. Rules:

- Reuse the existing `REQ-####` ID when the same requirement is clearly still present;
  mint a new ID only for genuinely new requirements.
- Down-scale before sending: a slide PNG wider than ~1600px on its long edge wastes
  vision tokens with no accuracy gain. `detect_changes.py` already caps width; do not
  up-res.
- Do NOT open slides in `unchanged`. Reuse their fragments from `.cache/manifest.json`.

Then assemble the full spec: cached fragments for unchanged slides + freshly extracted
fragments for changed slides → write `spec.yaml`.

### 3. Validate

```bash
python scripts/validate_spec.py spec.yaml
```

Fails loudly if any requirement is missing a required field (see `SPEC_SCHEMA.md`).
If it fails, name the specific `REQ-####` and its missing field and ask the user —
do not invent the missing content.

### 4. Diff against the previous version

```bash
python scripts/diff_spec.py OLD_spec.yaml spec.yaml --out delta.md
```

Produces a per-requirement change report (added / removed / modified, field by field)
that is safe to paste into a PR. This is the artifact developers read instead of
flipping through slides.

### 5. Regenerate acceptance criteria for changed requirements only

For every `REQ-####` that `diff_spec.py` marks added or modified, write AC using the
exact Given/When/Then structure in `AC_TEMPLATE.md`. Leave AC for unchanged
requirements untouched. Append/update them in `acceptance_criteria.md`.

### 6. Commit the set

Tell the user to commit `NEW.pptx`, `spec.yaml`, `.cache/manifest.json`,
`delta.md`, and `acceptance_criteria.md` together so the next version bump can diff
against this one.

## Reference files

- `SPEC_SCHEMA.md` — the exact shape of a requirement in `spec.yaml` (read before
  extracting).
- `AC_TEMPLATE.md` — Given/When/Then format with worked examples (read before writing
  AC).

## Dependencies

`libreoffice` (or `soffice`) and `pdftoppm` for rendering; Python `Pillow` and
`PyYAML`. `python-pptx` is used for XML-level hashing when present. All hashing is
pure-Python; no `imagehash` needed. If a tool is missing, tell the user rather than
falling back to full-deck vision.
