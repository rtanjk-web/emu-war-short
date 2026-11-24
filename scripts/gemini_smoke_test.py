#!/usr/bin/env python3
"""Official google-genai SDK smoke test using the Interactions API."""
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

if not os.environ.get("GEMINI_API_KEY"):
    sys.exit("GEMINI_API_KEY is not set. Add it to .env or the environment.")

from google import genai

client = genai.Client()  # picks up GEMINI_API_KEY automatically

MODELS = [
    "gemini-4-hydrogen",
    "gemini-4-carbon",
    "gemini-4-argon",
    "gemini-4-neon",
    "gemini-3.8-flash",
    "gemini-3.1-flash",
]
interaction = None
for model in MODELS:
    try:
        print(f"Trying {model} ...")
        interaction = client.interactions.create(
            model=model,
            input="Explain how AI works in a few words",
        )
        break
    except Exception as exc:
        print(f"  failed: {type(exc).__name__}: {str(exc)[:160]}")
if interaction is None:
    sys.exit("All models failed.")

print("--- interaction ---")
print("id:", interaction.id)
print("model:", interaction.model)
print("status:", interaction.status)
if getattr(interaction, "usage", None):
    print("usage:", interaction.usage)
print("--- output_text ---")
print(interaction.output_text)
