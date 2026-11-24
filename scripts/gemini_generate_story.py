#!/usr/bin/env python3
"""Generate a stickman Shorts storyboard JSON with Google Gemini (AI Studio API).

Usage:
  python gemini_generate_story.py "topic here"
  python gemini_generate_story.py            # uses default topic
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gemini_client import generate_text

ROOT = Path(__file__).resolve().parent.parent
PROMPT = ROOT / "prompts" / "gemini_story_prompt.txt"
OUT = ROOT / "sample" / "storyboard_gemini.json"
DEFAULT_TOPIC = "a golfer who hammered 327 dents into a new ball and won a village tournament"

CAMERAS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "diagonal"]


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOPIC
    prompt = PROMPT.read_text(encoding="utf-8").replace("{{TOPIC}}", topic)
    print("Generating storyboard with Gemini... topic:", topic)
    raw = generate_text(prompt, json_mode=True)
    data = parse_json(raw)

    # Normalize to our renderer schema.
    shots = []
    for i, s in enumerate(data.get("shots", []), 1):
        cam = s.get("camera") or CAMERAS[(i - 1) % len(CAMERAS)]
        if i > 1 and cam == shots[-1]["camera"]:
            cam = CAMERAS[i % len(CAMERAS)]
        shots.append({
            "id": i,
            "seconds": float(s.get("seconds", 4.0)),
            "beat": s.get("beat", "BEAT"),
            "narration": s.get("narration", "").strip(),
            "visual": s.get("visual", "").strip(),
            "camera": cam,
        })
    out = {
        "title": data.get("title", "Untitled"),
        "description": data.get("description", ""),
        "aspect": data.get("aspect", [1080, 1920]),
        "fps": int(data.get("fps", 30)),
        "style": data.get("style", "simple black stickman characters, round heads, dot eyes, thick outlines, flat bold backgrounds, 9:16"),
        "shots": shots,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT} ({len(shots)} shots, {sum(s['seconds'] for s in shots)}s, "
          f"{len(' '.join(s['narration'] for s in shots).split())} words)")


if __name__ == "__main__":
    main()
