#!/usr/bin/env python3
"""Stateful multi-turn example from https://aistudio.google.com/docs/get-started.md"""
from __future__ import annotations
import os, sys, time
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

MODELS = [
    "gemini-4-hydrogen",
    "gemini-4-carbon",
    "gemini-4-argon",
    "gemini-4-neon",
    "gemini-3.8-flash",
]


def create(model, **kwargs):
    last = None
    for attempt in range(4):
        try:
            return client.interactions.create(model=model, **kwargs)
        except Exception as exc:
            last = exc
            print(f"  retry {attempt+1} on {model}: {type(exc).__name__}: {str(exc)[:100]}", file=sys.stderr)
            time.sleep(1)
    raise last


# Pick a working model, then keep the same model for both turns so the
# previous_interaction_id belongs to the same model.
interaction1 = None
chosen_model = None
for model in MODELS:
    try:
        interaction1 = create(model, input="I have 2 dogs in my house.")
        chosen_model = model
        break
    except Exception as exc:
        print(f"  model {model} unavailable: {type(exc).__name__}", file=sys.stderr)
if interaction1 is None:
    sys.exit("All models failed for turn 1.")

print(f"[model: {chosen_model}]")
print("Response 1:", interaction1.output_text)

interaction2 = create(
    chosen_model,
    input="How many paws are in my house?",
    previous_interaction_id=interaction1.id,
)
print("Response 2:", interaction2.output_text)
print("Turn 1 id:", interaction1.id)
print("Turn 2 id:", interaction2.id)
