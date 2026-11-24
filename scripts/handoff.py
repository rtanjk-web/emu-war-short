#!/usr/bin/env python3
"""One-command handoff: AI Studio exports -> rendered 1080x1920 animatic.

Runs, in order:
  1. import_storyboard.py  (validate/copy pasted Playground JSON)
  2. map_images.py         (map downloaded images -> shot_01.png ... shot_NN.png)
  3. render_animatic.py    (Pillow frames + ffmpeg -> MP4)

Examples:
  python scripts/handoff.py --pasted pasted.json --images "C:\\Users\\rapha\\Downloads"
  python scripts/handoff.py --images ./downloads --skip-render   # prep assets only
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(SCRIPTS / script), *map(str, args)]
    print("\n>>>", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"FAILED: {script} (exit {result.returncode})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasted", help="JSON file exported/pasted from AI Studio Playground")
    ap.add_argument("--images", help="folder containing downloaded AI Studio images")
    ap.add_argument("--out", default=str(ROOT / "sample"), help="output project folder (default: sample)")
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--no-crop", action="store_true", help="keep source image aspect ratio")
    ap.add_argument("--skip-render", action="store_true", help="prepare JSON/assets but don't render MP4")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    storyboard = out / "storyboard.json"

    if args.pasted:
        run("import_storyboard.py", args.pasted, "--out", storyboard)
    elif not storyboard.exists():
        sys.exit(f"No storyboard at {storyboard}. Pass --pasted or create it first.")

    if args.images:
        extra = ["--no-crop"] if args.no_crop else []
        run("map_images.py", "--src", args.images, "--out", out / "assets",
            "--count", args.count, *extra)

    if not args.skip_render:
        run("render_animatic.py", storyboard, out)
        print(f"\nDONE: {out / 'animatic.mp4'}")


if __name__ == "__main__":
    main()
