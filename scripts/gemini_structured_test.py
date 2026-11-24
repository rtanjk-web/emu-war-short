#!/usr/bin/env python3
"""Structured output example from https://aistudio.google.com/docs/get-started.md"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
from typing import List, Optional

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

class Recipe(BaseModel):
    recipe_name: str = Field(description="Name of the recipe.")
    ingredients: List[str] = Field(description="List of ingredients.")
    prep_time_minutes: Optional[int] = Field(description="Prep time in minutes.")

client = genai.Client()

MODELS = ["gemini-4-hydrogen", "gemini-4-carbon", "gemini-4-argon", "gemini-4-neon", "gemini-3.8-flash"]
interaction = None
for attempt in range(4):
    for model in MODELS:
        try:
            interaction = client.interactions.create(
                model=model,
                input="Give me a recipe for banana bread",
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": Recipe.model_json_schema()
                },
            )
            print(f"[model: {model}]")
            break
        except Exception as exc:
            print(f"  retry {attempt+1} {model}: {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr)
            time.sleep(1)
    if interaction is not None:
        break

if interaction is None:
    sys.exit("All attempts failed.")

print("--- raw output_text ---")
print(interaction.output_text)
print("--- validated Pydantic model ---")
recipe = Recipe.model_validate_json(interaction.output_text)
print(recipe)
