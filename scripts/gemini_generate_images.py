#!/usr/bin/env python3
"""Replace placeholder frames with Gemini-generated stickman images.

Usage:
  python gemini_generate_images.py [storyboard.json] [limit]

Examples:
  python gemini_generate_images.py storyboard_gemini.json 2   # test first 2 shots
  python gemini_generate_images.py                            # all 8 shots
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gemini_client import generate_image

ROOT = Path(__file__).resolve().parent.parent


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "storyboard.json"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    sb_path = ROOT / "sample" / name
    sb = json.loads(sb_path.read_text(encoding="utf-8"))
    assets = ROOT / "sample" / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    # Fixed character sentences for consistency across every shot.
    characters = (
        "HERO: a simple black stickman with a round head, dot eyes and a yellow vest, "
        "holding a dented golf ball. RIVAL: a simple black stickman with a round head, "
        "dot eyes and a striped cap, holding a smooth golf ball."
    )

    for shot in sb["shots"][:limit]:
        prompt = (
            f"Use a consistent stickman style. {sb.get('style','')} "
            f"{characters} "
            f"SHOT {shot['id']} ({shot['beat']}): {shot['visual']} "
            f"Camera: {shot.get('camera','medium')}. "
            "Vertical 9:16 composition, single clear action, flat bold colors, "
            "generous negative space, no captions, no subtitles, no logos, no watermark. "
            "If a number is needed, show it on a sign or prop only."
        )
        print(f"Generating image for shot {shot['id']} ({shot['beat']})...")
        png = generate_image(prompt)
        out = assets / f"shot_{shot['id']:02d}.png"
        out.write_bytes(png)
        print(f"  wrote {out.name} ({len(png):,} bytes)")


if __name__ == "__main__":
    main()
