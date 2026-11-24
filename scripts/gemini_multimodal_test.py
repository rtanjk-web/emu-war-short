#!/usr/bin/env python3
"""Multimodal example from https://aistudio.google.com/docs/get-started.md"""
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

# Load a local image
with open(ROOT / "sample.jpg", "rb") as f:
    image_bytes = f.read()
image_b64 = base64.b64encode(image_bytes).decode("utf-8")

# The docs' sample.mp3 URL returns 404; use the public Apollo 11 sample instead.
AUDIO_URI = "https://storage.googleapis.com/generativeai-downloads/data/Apollo-11_Day-01-Highlights-10s.mp3"

payload = [
    {"type": "text", "text": "Compare this local image and this remote audio file."},
    {"type": "image", "data": image_b64, "mime_type": "image/jpeg"},
    {"type": "audio", "uri": AUDIO_URI, "mime_type": "audio/mp3"},
]

MODELS = ["gemini-4-hydrogen", "gemini-4-carbon", "gemini-4-argon", "gemini-4-neon", "gemini-3.8-flash"]
interaction = None
for attempt in range(4):
    for model in MODELS:
        try:
            interaction = client.interactions.create(model=model, input=payload)
            print(f"[model: {model}]")
            break
        except Exception as exc:
            print(f"  retry {attempt+1} {model}: {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr)
            time.sleep(1)
    if interaction is not None:
        break

if interaction is None:
    sys.exit("All attempts failed.")

print(interaction.output_text)
