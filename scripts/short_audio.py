#!/usr/bin/env python3
"""Voiceover + sound design for the Emu War short.

- TTS: gemini-3.8-flash-tts via the Interactions API (unary -> complete WAV).
- Music/SFX: synthesised with numpy so the mix is royalty-free and deterministic.

Usage:
  python scripts/short_audio.py --test "Australia once declared war on birds."
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import time
import wave
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
_last_call = 0.0
TTS_MODEL = "gemini-3.8-flash-tts"
API = "https://generativelanguage.googleapis.com/v1beta/interactions"


def load_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GEMINI_API_KEY not found (set it or add it to .env)")


def tts(text: str, out_wav: Path, voice: str = "Charon",
        style: str = "deadpan documentary narrator, dry and matter-of-fact",
        model: str = TTS_MODEL) -> float:
    """Synthesize one line and write a WAV. Returns duration in seconds."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha1(f"{model}|{voice}|{style}|{text}".encode()).hexdigest()[:16]
    cache = out_wav.parent / f"tts_{cache_key}.wav"
    if cache.exists():
        out_wav.write_bytes(cache.read_bytes())
        return wav_duration(out_wav)

    payload = {
        "model": model,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{"type": "speech_metadata", "style": style}],
            }],
        }],
        "response_format": {"type": "audio", "mime_type": "audio/wav", "sample_rate": 24000},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    global _last_call
    for attempt in range(4):
        wait = 21.0 - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        r = requests.post(API, headers={
            "x-goog-api-key": load_key(),
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        }, json=payload, timeout=180)
        _last_call = time.time()
        if r.status_code == 200:
            break
        if r.status_code == 429 and attempt < 3:
            m = re.search(r"retry in (\d+)", r.text)
            delay = int(m.group(1)) + 2 if m else 25
            print(f"    rate limited, waiting {delay}s...", flush=True)
            time.sleep(delay)
            continue
        raise RuntimeError(f"TTS {r.status_code}: {r.text[:400]}")
    data = r.json()
    blob = None
    for step in data.get("steps", []):
        for c in step.get("content", []):
            if c.get("type") in ("audio", "inline_data") and c.get("data"):
                blob = c["data"]
                break
        if blob:
            break
    if not blob:
        raise RuntimeError(f"no audio in response: {json.dumps(data)[:400]}")
    raw = base64.b64decode(blob)
    out_wav.write_bytes(raw)
    tighten(out_wav)
    cache.write_bytes(out_wav.read_bytes())
    return wav_duration(out_wav)


def tighten(path: Path, sr: int = 24000) -> float:
    """Trim edge silence and compress long internal pauses in place."""
    a = read_wav(path, sr)
    env = np.abs(a)
    idx = np.where(env > 0.015)[0]
    if len(idx) == 0:
        return 0.0
    a = a[max(0, idx[0] - int(0.05 * sr)): idx[-1] + int(0.10 * sr)]
    mask = np.abs(a) > 0.012
    keep = np.ones(len(a), dtype=bool)
    gap_max = int(0.16 * sr)
    i = 0
    n = len(mask)
    while i < n:
        if not mask[i]:
            j = i
            while j < n and not mask[j]:
                j += 1
            if j - i > gap_max:
                keep[i + gap_max:j] = False
            i = j
        else:
            i += 1
    a = a[keep]
    write_wav_mono(path, a, sr)
    return len(a) / sr


def write_wav_mono(path: Path, x: np.ndarray, sr: int) -> None:
    pcm = (np.clip(x, -1, 1) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def read_wav(path: Path, sr: int = SR) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        n, ch, sw, fr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        a = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if fr != sr:
        t = np.arange(int(len(a) * sr / fr)) * (fr / sr)
        a = np.interp(t, np.arange(len(a)), a).astype(np.float32)
    return a


def write_wav(path: Path, x: np.ndarray, sr: int = SR) -> None:
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        stereo = np.repeat(pcm[:, None], 2, axis=1)
        w.writeframes(stereo.tobytes())


# ---------------------------------------------------------------- synth
def t_axis(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def env_ad(n: int, attack: float, decay: float) -> np.ndarray:
    a = max(1, int(attack * SR))
    d = max(1, n - a)
    return np.concatenate([np.linspace(0, 1, a), np.exp(-np.linspace(0, 6, d)) * (1 - 0.0)])[:n]


def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    a = math.exp(-2 * math.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = a * acc + (1 - a) * x[i]
        y[i] = acc
    return y


def noise(dur: float, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, 1, int(dur * SR)).astype(np.float32)


def thud(dur: float = 0.32, f0: float = 95, f1: float = 42, amp: float = 0.5) -> np.ndarray:
    t = t_axis(dur)
    f = np.linspace(f0, f1, len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 11) * amp).astype(np.float32)


def click(freq: float = 1400, dur: float = 0.055, amp: float = 0.25) -> np.ndarray:
    t = t_axis(dur)
    return (np.sin(2 * np.pi * freq * t) * np.exp(-t * 70) * amp).astype(np.float32)


def whoosh(dur: float = 0.28, amp: float = 0.22) -> np.ndarray:
    n = int(dur * SR)
    x = noise(dur, seed=7)
    # sweep the one-pole cutoff upward by chunking
    out = np.empty(n, dtype=np.float32)
    acc = 0.0
    for i in range(n):
        cutoff = 300 + 4200 * (i / n) ** 2
        a = math.exp(-2 * math.pi * cutoff / SR)
        acc = a * acc + (1 - a) * x[i]
        out[i] = acc
    e = np.sin(np.linspace(0, math.pi, n)) ** 2
    return (out * e * amp * 3.0).astype(np.float32)


def gunfire(dur: float = 0.85, amp: float = 0.45) -> np.ndarray:
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(11)
    t = 0.0
    while t < dur - 0.06:
        d = 0.055
        seg = int(d * SR)
        i0 = int(t * SR)
        burst = rng.normal(0, 1, seg).astype(np.float32)
        burst = lowpass(burst, 2200) * np.exp(-np.linspace(0, 7, seg))
        out[i0:i0 + seg] += burst * amp * (0.9 if t < dur * 0.5 else 0.6)
        t += 0.075 + rng.random() * 0.045
    return out


def build_music(total: float, button_start: float) -> np.ndarray:
    """Sparse documentary bed: drone + woodblock pulse + kick."""
    n = int(total * SR)
    out = np.zeros(n, dtype=np.float32)
    t = np.arange(n) / SR

    # drone, fades in over 1.2s
    drone = (0.05 * np.sin(2 * np.pi * 55 * t) +
             0.035 * np.sin(2 * np.pi * 82.5 * t + 0.7))
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * t)
    drone *= np.clip(t / 1.2, 0, 1)
    # duck under the button line, then stop
    gate = np.ones(n, dtype=np.float32)
    b = int(button_start * SR)
    gate[b:] = 0.0
    out += (drone * gate).astype(np.float32)

    beat = 0.625  # 96 bpm
    k = 0
    while k * beat < total - 0.2:
        start = k * beat
        if start >= button_start:
            break
        # intensity ramps with time
        lvl = 0.55 + 0.45 * min(1.0, start / max(1.0, button_start))
        for sig in (click(1500, 0.05, 0.11 * lvl),):
            i0 = int(start * SR)
            out[i0:i0 + len(sig)] += sig
        if k % 2 == 0:
            s = thud(0.22, 105, 48, 0.16 * lvl)
            i0 = int(start * SR)
            out[i0:i0 + len(s)] += s
        k += 1

    # riser into the button
    r_dur = 1.6
    if button_start > r_dur:
        r = whoosh(r_dur, 0.10)
        i0 = int((button_start - r_dur) * SR)
        out[i0:i0 + len(r)] += r * np.linspace(0.4, 1.0, len(r))
    return out


def build_sfx(shots: list[dict]) -> np.ndarray:
    total = sum(s["seconds"] for s in shots)
    out = np.zeros(int(total * SR), dtype=np.float32)

    def add(sig: np.ndarray, at: float, gain: float = 1.0) -> None:
        i0 = int(at * SR)
        i1 = min(len(out), i0 + len(sig))
        if i0 < len(out):
            out[i0:i1] += sig[:i1 - i0] * gain

    add(thud(0.45, 110, 40, 0.55), 0.0, 1.0)  # hook impact
    t = 0.0
    for i, s in enumerate(shots):
        dur = s["seconds"]
        if i > 0:
            add(whoosh(0.26, 0.20), t - 0.10, 0.9)
        if i == 4:  # the ambush
            add(gunfire(0.9, 0.40), t + 0.05, 1.0)
        if i == 5:  # the jam
            add(click(300, 0.20, 0.30), t + 0.02, 1.0)
        t += dur
    return out


def stretch(path: Path, tempo: float) -> None:
    """Pitch-preserving time stretch via ffmpeg atempo."""
    import subprocess
    ff = os.environ.get("FFMPEG_BIN")
    if not ff:
        hits = sorted((Path.home() / "AppData/Local/CapCut/Apps").rglob("ffmpeg.exe"))
        ff = str(hits[-1]) if hits else "ffmpeg"
    tmp = path.with_suffix(".tmp.wav")
    subprocess.run([ff, "-y", "-i", str(path), "-filter:a", f"atempo={tempo:.4f}",
                    "-ar", "24000", "-ac", "1", str(tmp)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp.replace(path)


def prepare_shots(storyboard: dict, work: Path, pad: float = 0.30) -> list[dict]:
    shots, t = [], 0.0
    for shot in storyboard["shots"]:
        wav = work / f"vo_{shot['id']:02d}.wav"
        dur = tts(shot["narration"], wav, storyboard.get("voice", "Charon"),
                  storyboard.get("style_note", "deadpan documentary narrator"),
                  storyboard.get("tts_model", TTS_MODEL))
        tempo = float(shot.get("tempo", 1.0))
        if abs(tempo - 1.0) > 1e-3:
            stretch(wav, tempo)
            dur = wav_duration(wav)
        seg = max(1.9, dur + pad)
        shots.append({**shot, "vo_dur": dur, "seconds": round(seg, 3), "start": round(t, 3)})
        t += seg
    return shots


def prepare_shots_offline(storyboard: dict, work: Path, pad: float = 0.30) -> list[dict]:
    """Same timing as prepare_shots, but reads existing voice files only.

    Used by CI so a render never depends on TTS quota or a live API key.
    """
    shots, t = [], 0.0
    for shot in storyboard["shots"]:
        wav = work / f"vo_{shot['id']:02d}.wav"
        if not wav.exists():
            raise SystemExit(f"missing voiceover {wav} - run once without --offline")
        dur = wav_duration(wav)
        seg = max(1.9, dur + pad)
        shots.append({**shot, "vo_dur": dur, "seconds": round(seg, 3), "start": round(t, 3)})
        t += seg
    return shots


def mix_timed(storyboard: dict, shots: list[dict], out_wav: Path, work: Path) -> float:
    total = sum(s["seconds"] for s in shots) + 0.45
    n = int(total * SR)

    def fit(x: np.ndarray) -> np.ndarray:
        """Pad or truncate a stem to the master length so summing always works."""
        y = np.zeros(n, dtype=np.float32)
        m = min(n, len(x))
        if m > 0:
            y[:m] = x[:m]
        return y

    voice = np.zeros(n, dtype=np.float32)
    for s in shots:
        a = read_wav(work / f"vo_{s['id']:02d}.wav")
        a = a - a.mean()  # remove any DC offset
        i0 = int(s["start"] * SR)
        i1 = min(n, i0 + len(a))
        voice[i0:i1] += a[: i1 - i0] * 0.92

    music = fit(build_music(total, shots[-1]["start"]))
    sfx = fit(build_sfx(shots))
    mix = voice + music * 0.55 + sfx

    peak = float(np.max(np.abs(mix))) or 1.0
    if peak > 0.95:
        mix *= 0.95 / peak
    write_wav(out_wav, mix)
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", help="synthesize one line")
    ap.add_argument("--out", default=str(ROOT / "sample" / "vo_test.wav"))
    args = ap.parse_args()
    if args.test:
        d = tts(args.test, Path(args.out))
        print(f"wrote {args.out} ({d:.2f}s)")
