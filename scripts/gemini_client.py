#!/usr/bin/env python3
"""Minimal Google AI Studio (Gemini API) REST client. No third-party SDK needed.

Uses GEMINI_API_KEY from .env (or environment). Uses `requests` only.
"""
from __future__ import annotations
import base64, json, os
from io import BytesIO
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://generativelanguage.googleapis.com/v1beta"


def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_key() -> str:
    load_env()
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY in .env or as environment variable.")
    return key


def _request(method: str, path: str, *, params=None, payload=None, timeout=120):
    load_env()
    url = f"{BASE}/{path}"
    kwargs = {"params": {"key": get_key(), **(params or {})}, "timeout": timeout}
    if payload is not None:
        kwargs["json"] = payload
    r = requests.request(method, url, **kwargs)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini API {r.status_code} on {path}: {r.text[:1200]}")
    return r.json()


def list_models() -> list[dict]:
    data = _request("GET", "models")
    return data.get("models", [])


def generate_text(prompt: str, model="gemini-2.5-flash", temperature=0.8,
                  max_tokens=8192, json_mode=False) -> str:
    gen: dict = {"temperature": temperature, "maxOutputTokens": max_tokens}
    if json_mode:
        gen["responseMimeType"] = "application/json"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": gen,
    }
    data = _request("POST", f"models/{model}:generateContent", payload=payload)
    parts = []
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "text" in part:
                parts.append(part["text"])
    if not parts:
        raise RuntimeError("No text returned: " + json.dumps(data)[:1200])
    return "".join(parts)


def generate_image(prompt: str, model="gemini-2.5-flash-image") -> bytes:
    """Return PNG bytes (Gemini 2.5 Flash Image / Nano Banana)."""
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    data = _request("POST", f"models/{model}:generateContent", payload=payload, timeout=180)
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "inlineData" in part and part["inlineData"].get("data"):
                raw = base64.b64decode(part["inlineData"]["data"])
                from PIL import Image
                img = Image.open(BytesIO(raw)).convert("RGB")
                out = BytesIO()
                img.save(out, format="PNG")
                return out.getvalue()
    raise RuntimeError("No image returned: " + json.dumps(data)[:1200])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "models":
        for m in list_models():
            print(m.get("name"), "|", m.get("displayName"))
    elif len(sys.argv) > 2 and sys.argv[1] == "text":
        print(generate_text(sys.argv[2]))
    else:
        print("Usage: python gemini_client.py models | text 'prompt'")
