#!/usr/bin/env python3
"""Map downloaded AI Studio images into shot_01.png ... shot_08.png.

Reads image files from a source folder (default: your Downloads folder),
detects shot numbers in filenames (e.g. 'shot 3.png', 'shot_03.jpg',
'frame-2.png'), and fills any remaining slots in file-modification order.
Images are converted to PNG and centre-cropped to 1080x1920 for the renderer.

Usage:
  python scripts/map_images.py --src "C:\\Users\\rapha\\Downloads"
  python scripts/map_images.py --src ./downloads --count 8 --no-crop
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def detect_number(stem: str, count: int) -> int | None:
    low = stem.lower()
    candidates: list[int] = []
    if "shot" in low or "frame" in low:
        candidates += [int(n) for n in re.findall(r"(\d{1,2})", low)]
    m = re.search(r"(?:^|[\s_\-])(\d{1,2})(?=$|[\s_\-])", low)
    if m:
        candidates.append(int(m.group(1)))
    for n in candidates:
        if 1 <= n <= count:
            return n
    return None


def cover_crop(img: Image.Image, size=(1080, 1920)) -> Image.Image:
    tw, th = size
    w, h = img.size
    target = tw / th
    if w / h > target:
        nw = int(h * target)
        left = (w - nw) // 2
        img = img.crop((left, 0, left + nw, h))
    else:
        nh = int(w / target)
        top = (h - nh) // 2
        img = img.crop((0, top, w, top + nh))
    return img.resize(size, Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(Path.home() / "Downloads"))
    ap.add_argument("--out", default=str(ROOT / "sample" / "assets"))
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--no-crop", action="store_true", help="keep source aspect ratio (renderer will scale)")
    args = ap.parse_args()

    src = Path(args.src)
    out_dir = Path(args.out)
    if not src.is_dir():
        raise SystemExit(f"Source folder not found: {src}")
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [p for p in (src.rglob("*") if args.recursive else src.iterdir())
             if p.is_file() and p.suffix.lower() in EXTS]
    if not files:
        raise SystemExit(f"No images found in {src}")

    assigned: dict[int, Path] = {}
    leftovers: list[Path] = []
    for p in files:
        n = detect_number(p.stem, args.count)
        if n and n not in assigned:
            assigned[n] = p
        else:
            leftovers.append(p)
    leftovers.sort(key=lambda p: p.stat().st_mtime)
    for p in leftovers:
        for n in range(1, args.count + 1):
            if n not in assigned:
                assigned[n] = p
                break

    print(f"Found {len(files)} image(s) in {src}")
    for n in range(1, args.count + 1):
        target = out_dir / f"shot_{n:02d}.png"
        source = assigned.get(n)
        if source is None:
            print(f"  shot {n:02d}: MISSING (keeping existing file if any)")
            continue
        img = Image.open(source).convert("RGB")
        if not args.no_crop:
            img = cover_crop(img)
        img.save(target, format="PNG")
        print(f"  shot {n:02d}: {source.name} -> {target.name}")

    missing = [n for n in range(1, args.count + 1) if n not in assigned]
    if missing:
        print(f"WARNING: no source image for shot(s) {missing}")


if __name__ == "__main__":
    main()
