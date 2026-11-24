#!/usr/bin/env python3
"""Streaming example from https://aistudio.google.com/docs/get-started.md"""
from __future__ import annotations
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import time
from google import genai

client = genai.Client()

MODELS = [
    "gemini-4-hydrogen",
    "gemini-4-carbon",
    "gemini-4-argon",
    "gemini-4-neon",
    "gemini-3.8-flash",
]
stream = None
for attempt in range(3):
    for model in MODELS:
        try:
            stream = client.interactions.create(
                model=model,
                input="Explain how AI works",
                stream=True,
            )
            print(f"[using model: {model}]")
            break
        except Exception as exc:
            print(f"[retry {attempt+1}] {model}: {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr)
            time.sleep(1)
    if stream is not None:
        break

if stream is None:
    sys.exit("All streaming attempts failed.")

count = 0
for event in stream:
    print(event)
    count += 1
print(f"[stream ended: {count} events]")
