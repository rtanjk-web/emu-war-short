#!/usr/bin/env python3
"""Generate a validated stickman storyboard with the Interactions API + structured output.

Usage:
  python scripts/gemini_story_structured.py "topic" [output.json]
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from google import genai
from pydantic import BaseModel, Field

class Shot(BaseModel):
    id: int = Field(description="1-based shot number")
    seconds: float = Field(description="duration in seconds, use 4.0")
    beat: str = Field(description="HOOK, SETUP, DOUBT, ESCALATE, TURN, REVEAL or BUTTON")
    narration: str = Field(description="one sentence of voiceover narration")
    visual: str = Field(description="exactly what the camera sees, one clear action")
    camera: str = Field(description="zoom_in, zoom_out, pan_left, pan_right or diagonal")

class Storyboard(BaseModel):
    title: str = Field(description="4-8 word title")
    description: str = Field(description="2-3 sentence YouTube description with the true fact and 3 hashtags")
    style: str = Field(description="short visual style sentence for stickman characters")
    shots: List[Shot] = Field(description="exactly 8 shots")

DEFAULT_TOPIC = "a golfer who hammered 327 dents into a new ball before a village tournament"
PROMPT_FILE = ROOT / "prompts" / "gemini_story_prompt.txt"

topic = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOPIC
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "sample" / "storyboard_gemini.json"
base_prompt = PROMPT_FILE.read_text(encoding="utf-8").replace("{{TOPIC}}", topic)
prompt = (
    base_prompt
    + "\n\nReturn the storyboard using the requested structured output schema. "
      "The style field must start: 'simple black stickman characters, round heads, dot eyes, thick outlines'."
)

client = genai.Client()
MODELS = ["gemini-4-hydrogen", "gemini-4-carbon", "gemini-4-argon", "gemini-3.8-flash"]
interaction = None
for attempt in range(3):
    for model in MODELS:
        try:
            interaction = client.interactions.create(
                model=model,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": Storyboard.model_json_schema(),
                },
            )
            print(f"[model: {model}]")
            break
        except Exception as exc:
            print(f"  retry {attempt+1} {model}: {type(exc).__name__}: {str(exc)[:140]}", file=sys.stderr)
            time.sleep(1)
    if interaction is not None:
        break
if interaction is None:
    sys.exit("All attempts failed.")

board = Storyboard.model_validate_json(interaction.output_text)
data = board.model_dump()
data["aspect"] = [1080, 1920]
data["fps"] = 30
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(__import__("json").dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_path}: {len(data['shots'])} shots, {sum(s['seconds'] for s in data['shots'])}s, "
      f"{len(' '.join(s['narration'] for s in data['shots']).split())} words")
print("Title:", data["title"])
