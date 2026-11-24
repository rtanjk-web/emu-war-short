#!/usr/bin/env python3
"""Image generation example from https://aistudio.google.com/docs/get-started.md"""
from __future__ import annotations
import base64, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from google import genai

client = genai.Client()

PROMPT = "Generate an image of a futuristic city skyline at sunset"
MODELS = [
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-nano-banana-2.1",
    "gemini-2.5-flash-image",
]

interaction = None
for attempt in range(4):
    for model in MODELS:
        try:
            interaction = client.interactions.create(model=model, input=PROMPT)
            print(f"[model: {model}]")
            break
        except Exception as exc:
            print(f"  retry {attempt+1} {model}: {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr)
            time.sleep(1)
    if interaction is not None:
        break

if interaction is None:
    sys.exit("All attempts failed.")

if interaction.output_image is None or not interaction.output_image.data:
    sys.exit("No image returned. output_text: " + str(interaction.output_text)[:500])

out = ROOT / "generated_image.png"
with open(out, "wb") as f:
    f.write(base64.b64decode(interaction.output_image.data))
print("wrote", out, out.stat().st_size, "bytes")
print("mime:", interaction.output_image.mime_type)
