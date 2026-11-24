#!/usr/bin/env python3
"""Managed agent example from https://aistudio.google.com/docs/get-started.md"""
from __future__ import annotations
import os, time
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

client = genai.Client(http_options={"api_version": "v1beta"})

t = time.time()
interaction = client.interactions.create(
    agent="antigravity-preview-09-2026",
    input="Write a Python script that generates the first 20 Fibonacci numbers and saves them to fibonacci.txt. Then read the file and print its contents.",
    environment="remote",
)
print(f"completed in {time.time()-t:.1f}s")
print(f"Environment: {interaction.environment_id}")
print(interaction.output_text)
