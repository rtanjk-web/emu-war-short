#!/usr/bin/env python3
"""Image-to-video with Gemini Omni 1.2 Flash — animate a local stickman frame.

Source: https://aistudio.google.com/docs/omni.md#image-to-video-generation
BLOCKED on current Free Tier key (0 requests/day for gemini-omni-1.2-flash).

Usage:
  python scripts/gemini_image_to_video.py [image_path] [output.mp4]
"""
from __future__ import annotations
import base64, os, sys
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

image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sample" / "assets" / "shot_01.png"
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "sample" / "video_shot_01.mp4"
mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

client = genai.Client()
image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")

interaction = client.interactions.create(
    model="gemini-omni-1.2-flash",
    input=[
        {"type": "image", "data": image_b64, "mime_type": mime},
        {"type": "text", "text": (
            "Animate this stickman illustration with simple, expressive motion: "
            "the golfer swings the hammer down onto the dimpled ball, then the ball "
            "flies forward. Keep the flat black stickman style and bold colors exactly "
            "as in the reference image. Smooth camera push-in. No text, no captions, "
            "no watermark. Native ambient sound effects only."
        )},
    ],
    response_format={"type": "video", "aspect_ratio": "9:16", "duration": "4s", "resolution": "720p"},
)

out_path.write_bytes(base64.b64decode(interaction.output_video.data))
print("wrote", out_path, out_path.stat().st_size, "bytes")
