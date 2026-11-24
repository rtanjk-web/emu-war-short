#!/usr/bin/env python3
"""Generate a normalized storyboard JSON from a simple input file.

Input JSON format:
{
  "title": "...",
  "description": "...",
  "shots": [{"narration":"...","visual":"...","beat":"HOOK","seconds":4.0,"camera":"zoom_in"}]
}

Usage:
  python generate_storyboard.py input.json output.json
"""
from __future__ import annotations
import json, sys, pathlib

CAMERAS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "diagonal"]

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_storyboard.py input.json output.json")
        sys.exit(2)
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))
    shots = data.get("shots", [])
    norm = []
    for i, s in enumerate(shots, 1):
        cam = s.get("camera") or CAMERAS[(i - 1) % len(CAMERAS)]
        if i > 1 and cam == norm[-1]["camera"]:
            cam = CAMERAS[i % len(CAMERAS)]
        norm.append({
            "id": i,
            "seconds": float(s.get("seconds", 4.0)),
            "beat": s.get("beat", "BEAT"),
            "narration": s.get("narration", "").strip(),
            "visual": s.get("visual", "").strip(),
            "camera": cam,
        })
    out = {
        "title": data.get("title", "Untitled Stickman Short"),
        "description": data.get("description", ""),
        "aspect": data.get("aspect", [1080, 1920]),
        "fps": int(data.get("fps", 30)),
        "style": data.get("style", "simple black stickman characters, round heads, dot eyes, thick outlines, flat bold backgrounds, 9:16"),
        "shots": norm,
        "total_seconds": round(sum(s["seconds"] for s in norm), 2),
        "word_count": len(" ".join(s["narration"] for s in norm).split()),
    }
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {dst} ({len(norm)} shots, {out['total_seconds']}s, {out['word_count']} words)")

if __name__ == "__main__":
    main()
