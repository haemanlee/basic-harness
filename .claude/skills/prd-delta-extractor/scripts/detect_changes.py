#!/usr/bin/env python3
"""Detect which slides in a .pptx changed versus the previous version, WITHOUT vision.

Pipeline (all local / CPU-only, no tokens):
  1. Render each slide to PNG via libreoffice -> pdf -> pdftoppm.
  2. Hash each slide two ways:
       - xml_hash:  normalized slide XML from the pptx zip (exact, cheap)
       - dhash:     perceptual difference-hash of the PNG (fallback for decks whose
                    XML churns without visible change)
  3. Compare against .cache/manifest.json from the previous version.
  4. Emit changes.json: {changed, unchanged, png_dir, first_run} and update the manifest.

A slide counts as UNCHANGED only if its xml_hash matches, OR (when xml differs) its
dhash is within HAMMING_THRESHOLD of the cached dhash. Everything else is CHANGED.

Usage:
    python detect_changes.py NEW.pptx --cache .cache --out changes.json
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image

# A slide whose PNG differs from the cached PNG by more than this many bits (out of 64)
# is treated as a real visual change. Small values catch subtle edits; too small and
# rendering jitter creates false positives. 5 is a conservative default.
HAMMING_THRESHOLD = 5
# Cap PNG width so the vision step downstream isn't handed needlessly large images.
MAX_PNG_WIDTH = 1600


def _run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr}")
    return proc.stdout


def find_soffice():
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(
        "libreoffice/soffice not found. Install it (or tell the user) — do NOT fall "
        "back to sending the whole deck to vision."
    )


def render_slides(pptx: Path, work: Path) -> list[Path]:
    """pptx -> per-slide PNGs, capped to MAX_PNG_WIDTH. Returns sorted PNG paths."""
    work.mkdir(parents=True, exist_ok=True)
    soffice = find_soffice()
    # pptx -> pdf
    _run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(work), str(pptx)])
    pdf = work / (pptx.stem + ".pdf")
    if not pdf.exists():
        raise RuntimeError(f"libreoffice did not produce {pdf}")
    # pdf -> png per page (pdftoppm zero-pads and 1-indexes: slide-1.png ...)
    prefix = work / "slide"
    if shutil.which("pdftoppm") is None:
        raise RuntimeError("pdftoppm not found; install poppler-utils.")
    _run(["pdftoppm", "-r", "110", "-png", str(pdf), str(prefix)])
    pngs = sorted(work.glob("slide-*.png"), key=_page_num)
    for p in pngs:
        _downscale(p)
    return pngs


def _page_num(p: Path) -> int:
    m = re.search(r"slide-(\d+)", p.stem)
    return int(m.group(1)) if m else 0


def _downscale(png: Path):
    img = Image.open(png)
    if img.width > MAX_PNG_WIDTH:
        h = round(img.height * MAX_PNG_WIDTH / img.width)
        img = img.resize((MAX_PNG_WIDTH, h), Image.LANCZOS)
        img.save(png)


def normalized_slide_xml_hashes(pptx: Path) -> dict[int, str]:
    """Map 1-based slide index -> sha1 of normalized slide XML.

    Normalization strips volatile bits (whitespace runs, r:embed rId numbers) so that
    re-saving a deck without content changes doesn't register as a diff.
    """
    out: dict[int, str] = {}
    with zipfile.ZipFile(pptx) as z:
        names = [n for n in z.namelist()
                 if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        for n in names:
            idx = int(re.search(r"slide(\d+)\.xml", n).group(1))
            xml = z.read(n).decode("utf-8", "replace")
            xml = re.sub(r'r:embed="rId\d+"', 'r:embed="rId"', xml)
            xml = re.sub(r'r:id="rId\d+"', 'r:id="rId"', xml)
            xml = re.sub(r"\s+", " ", xml).strip()
            out[idx] = hashlib.sha1(xml.encode()).hexdigest()
    return out


def dhash(png: Path, size: int = 8) -> str:
    """64-bit perceptual difference hash as a 16-char hex string."""
    img = Image.open(png).convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(img.tobytes())  # one byte per pixel, row-major (== getdata for mode "L")
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return f"{bits:016x}"


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--cache", type=Path, default=Path(".cache"))
    ap.add_argument("--out", type=Path, default=Path("changes.json"))
    args = ap.parse_args()

    if not args.pptx.exists():
        sys.exit(f"no such file: {args.pptx}")

    cache = args.cache
    png_dir = cache / "png"
    manifest_path = cache / "manifest.json"
    if png_dir.exists():
        shutil.rmtree(png_dir)
    cache.mkdir(parents=True, exist_ok=True)

    prev = {}
    if manifest_path.exists():
        prev = json.loads(manifest_path.read_text()).get("slides", {})
    first_run = not prev

    pngs = render_slides(args.pptx, png_dir)
    xml_hashes = normalized_slide_xml_hashes(args.pptx)

    changed, unchanged, slides_manifest = [], [], {}
    for png in pngs:
        idx = _page_num(png)
        xh = xml_hashes.get(idx, "")
        dh = dhash(png)
        combined = hashlib.sha1(f"{xh}:{dh}".encode()).hexdigest()[:8]
        slides_manifest[str(idx)] = {"xml_hash": xh, "dhash": dh, "source_hash": combined}

        p = prev.get(str(idx))
        if p is None:
            changed.append(idx)
        elif p.get("xml_hash") and xh:
            # XML is authoritative when available on both sides: any XML change is a
            # real content change. dHash must NOT suppress it (that would be a false
            # negative -> wrong AC). dHash is only a fallback for missing XML below.
            (unchanged if p["xml_hash"] == xh else changed).append(idx)
        elif p.get("dhash") and hamming(p["dhash"], dh) <= HAMMING_THRESHOLD:
            unchanged.append(idx)
        else:
            changed.append(idx)

    # Slides that existed before but are gone now (keys are strings on both sides).
    removed = sorted(int(i) for i in prev if i not in slides_manifest)

    manifest_path.write_text(json.dumps(
        {"pptx": args.pptx.name, "slides": slides_manifest}, indent=2, ensure_ascii=False))

    result = {
        "changed": sorted(changed),
        "unchanged": sorted(unchanged),
        "removed": removed,
        "png_dir": str(png_dir),
        "first_run": first_run,
    }
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    n = len(changed)
    total = len(pngs)
    print(f"{total} slides | changed: {n} -> {sorted(changed)} | "
          f"unchanged: {len(unchanged)} | removed: {removed}")
    print(f"vision needed on {n}/{total} slides. wrote {args.out}")


if __name__ == "__main__":
    main()
