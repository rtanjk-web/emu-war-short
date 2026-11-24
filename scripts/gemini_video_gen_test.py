#!/usr/bin/env python3
"""Text-to-video with Gemini Omni 1.2 Flash (Interactions API).

Source: https://aistudio.google.com/docs/omni.md
BLOCKED on current Free Tier key: gemini-omni-1.2-flash returns
429 "limit: 0 requests per day". Enable billing at https://ai.dev/rate-limit.

Usage:
  python scripts/gemini_video_gen_test.py
"""
from __future__ import annotations
import base64, os
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

interaction = client.interactions.create(
    model="gemini-omni-1.2-flash",
    input="A marble rolling fast on a chain reaction style track, continuous smooth shot.",
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",   # 9:16 or 16:9 (default 16:9)
        "duration": "4s",          # 3s-15s; default 10s
        "resolution": "720p",      # 360p / 720p / 1080p / 4k
    },
)

out = ROOT / "omni_marble_9x16.mp4"
out.write_bytes(base64.b64decode(interaction.output_video.data))
print("wrote", out, out.stat().st_size, "bytes")
print("interaction:", interaction.id)
