#!/usr/bin/env python3
"""Validate and normalize a storyboard JSON pasted from AI Studio Playground.

Usage:
  python scripts/import_storyboard.py pasted.json
  python scripts/import_storyboard.py pasted.json --out sample/storyboard.json
  Get-Content pasted.json -Raw | python scripts/import_storyboard.py -

Hard errors (exit 1): unparseable JSON, missing/empty shots, missing narration.
Warnings (exit 0): hook/word-count/beat-order issues — the render still works.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMERAS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "diagonal"]
EXPECTED_BEATS = ["HOOK", "SETUP", "DOUBT", "ESCALATE", "ESCALATE", "TURN", "REVEAL", "BUTTON"]
BAD_STARTS = ("how ", "what ", "why ", "did you ", "imagine ", "ever ")


def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="JSON file, or '-' to read stdin")
    ap.add_argument("--out", default=str(ROOT / "sample" / "storyboard.json"))
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    try:
        data = json.loads(strip_fences(raw))
    except Exception as exc:
        sys.exit(f"ERROR: invalid JSON: {exc}")

    shots_in = data.get("shots")
    if not isinstance(shots_in, list) or not shots_in:
        sys.exit("ERROR: 'shots' must be a non-empty list.")
    for i, s in enumerate(shots_in, 1):
        if not isinstance(s, dict) or not str(s.get("narration", "")).strip():
            sys.exit(f"ERROR: shot {i} has no narration.")

    warnings: list[str] = []
    shots = []
    prev_cam = None
    for i, s in enumerate(shots_in, 1):
        cam = str(s.get("camera") or CAMERAS[(i - 1) % len(CAMERAS)]).strip()
        if cam not in CAMERAS:
            warnings.append(f"shot {i}: unknown camera '{cam}' -> '{CAMERAS[(i-1) % len(CAMERAS)]}'")
            cam = CAMERAS[(i - 1) % len(CAMERAS)]
        if cam == prev_cam:
            cam = CAMERAS[i % len(CAMERAS)]
            warnings.append(f"shot {i}: camera repeated, changed to '{cam}'")
        prev_cam = cam
        try:
            secs = float(s.get("seconds", 4.0))
        except (TypeError, ValueError):
            secs = 4.0
            warnings.append(f"shot {i}: bad seconds, using 4.0")
        shots.append({
            "id": i,
            "seconds": secs,
            "beat": str(s.get("beat") or "BEAT").strip().upper(),
            "narration": str(s.get("narration", "")).strip(),
            "visual": str(s.get("visual", "")).strip(),
            "camera": cam,
        })

    total_words = len(" ".join(s["narration"] for s in shots).split())
    hook = shots[0]["narration"]
    if not 85 <= total_words <= 115:
        warnings.append(f"total narration {total_words} words; 30s target is ~100 (85-115).")
    if not 5 <= len(hook.split()) <= 18:
        warnings.append(f"hook is {len(hook.split())} words; target 5-18.")
    if hook.lower().startswith(BAD_STARTS) or hook.strip().endswith("?"):
        warnings.append("hook starts with a banned opener or is a question.")
    if len(shots) == len(EXPECTED_BEATS):
        beats = [s["beat"] for s in shots]
        if beats != EXPECTED_BEATS:
            warnings.append(f"beat order differs from recommended: {beats}")
    reveal = [s for s in shots if s["beat"] == "REVEAL"]
    if reveal and not reveal[0]["narration"].lower().startswith("you see,"):
        warnings.append("REVEAL sentence should start with 'You see,'")

    out = {
        "title": str(data.get("title", "Untitled Stickman Short")),
        "description": str(data.get("description", "")),
        "aspect": data.get("aspect", [1080, 1920]),
        "fps": int(data.get("fps", 30)),
        "style": str(data.get("style", "simple black stickman characters, round heads, dot eyes, thick outlines, flat bold backgrounds, 9:16")),
        "shots": shots,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Imported {len(shots)} shots, {sum(s['seconds'] for s in shots)}s, {total_words} words -> {out_path}")
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings:
            print("  -", w)
    else:
        print("No warnings.")


if __name__ == "__main__":
    main()
