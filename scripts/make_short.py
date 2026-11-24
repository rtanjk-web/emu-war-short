#!/usr/bin/env python3
"""Render the Emu War short end to end.

  python scripts/make_short.py --story sample/emu_storyboard.json --out sample/emu
  python scripts/make_short.py --story sample/emu_storyboard.json --out sample/emu --preview 4

Pipeline: TTS per shot -> exact durations -> animated flat-vector frames with
camera moves + karaoke captions -> h264 segments -> concat -> mix -> mux.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import short_art as A  # noqa: E402
import short_audio as S  # noqa: E402

W, H, FPS = 1080, 1920, 30

# z0, z1, panx0, panx1, pany0, pany1  (design px)
MOVES = {
    "zoom_in":   (1.00, 1.13, 0, 0, 0, 0),
    "zoom_out":  (1.13, 1.00, 0, 0, 0, 0),
    "pan_left":  (1.08, 1.08, 30, -30, 0, 0),
    "pan_right": (1.08, 1.08, -30, 30, 0, 0),
    "diagonal":  (1.02, 1.14, -18, 18, 12, -12),
}


def find_ffmpeg() -> str:
    p = shutil.which("ffmpeg")
    if p:
        return p
    cand = Path.home() / "AppData/Local/CapCut/Apps"
    if cand.exists():
        hits = sorted(cand.rglob("ffmpeg.exe"))
        if hits:
            return str(hits[-1])
    raise FileNotFoundError("ffmpeg not found")


_ENCODER: list[str] | None = None


def pick_encoder(ffmpeg: str) -> list[str]:
    """Choose the best H.264 encoder this ffmpeg build actually has.

    CapCut's Windows ffmpeg ships h264_mf (Media Foundation) but no libx264;
    stock Linux/Homebrew builds are the other way round.
    """
    try:
        out = subprocess.run([ffmpeg, "-hide_banner", "-encoders"],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        out = ""
    if "h264_mf" in out:
        return ["-c:v", "h264_mf", "-b:v", "9M"]
    if "libx264" in out:
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
    return ["-c:v", "h264", "-b:v", "9M"]


def encoder_args(ffmpeg: str) -> list[str]:
    global _ENCODER
    if _ENCODER is None:
        _ENCODER = pick_encoder(ffmpeg)
        print("encoder:", " ".join(_ENCODER), flush=True)
    return _ENCODER


def ease(p: float) -> float:
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def camera(move: str, p: float, focus: tuple[float, float]):
    z0, z1, px0, px1, py0, py1 = MOVES[move]
    e = ease(p)
    z = z0 + (z1 - z0) * e
    cx = focus[0] + px0 + (px1 - px0) * e
    cy = focus[1] + py0 + (py1 - py0) * e
    cw, ch = W / z, H / z
    cx = min(max(cx, cw / 2), W - cw / 2)
    cy = min(max(cy, ch / 2), H - ch / 2)
    return z, cx, cy


def frame(src: Image.Image, move: str, p: float, focus) -> Image.Image:
    z, cx, cy = camera(move, p, focus)
    cw, ch = W / z, H / z
    x0 = (cx - cw / 2) * A.SS
    y0 = (cy - ch / 2) * A.SS
    a = (cw * A.SS) / W
    return src.transform((W, H), Image.Transform.AFFINE, (a, 0, x0, 0, a, y0),
                         resample=Image.Resampling.BICUBIC)


# ---------------------------------------------------------------- captions
CFONT = A.load_font(84)
SPACE = CFONT.getlength(" ")


def wrap_caption(words: list[str], max_w: float = 840) -> list[list[str]]:
    lines, cur = [], []
    for w in words:
        trial = cur + [w]
        if cur and CFONT.getlength(" ".join(trial)) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def word_times(words: list[str], span: float):
    weights = []
    for w in words:
        k = len(w) + 1.2
        if w[-1] in ".!?":
            k += 3.4
        elif w[-1] in ",;:":
            k += 1.6
        weights.append(k)
    tot = sum(weights)
    out, t = [], 0.0
    for k in weights:
        d = span * k / tot
        out.append((t, t + d))
        t += d
    return out


def draw_caption(img: Image.Image, words: list[str], times, lines, t: float) -> None:
    if not words:
        return
    idx = 0
    for i, (a, _) in enumerate(times):
        if t >= a:
            idx = i
    li, start = 0, 0
    for j, line in enumerate(lines):
        if idx < start + len(line):
            li = j
            break
        start += len(line)
    line = lines[li]

    text = " ".join(line)
    tw = CFONT.getlength(text)
    pad_x, bh = 36, 128
    bw = min(W - 40, tw + 2 * pad_x)
    cx, cy = W / 2, 1520
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2],
                        radius=26, fill=A.INK)
    x = cx - tw / 2
    for k, word in enumerate(line):
        wi = start + k
        color = A.ACCENT if wi == idx else A.PAPER
        d.text((x, cy), word, font=CFONT, fill=color, anchor="lm")
        x += CFONT.getlength(word) + SPACE


# ---------------------------------------------------------------- encode
def encode(ffmpeg: str, frames, out: Path) -> None:
    cmd = [ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    cmd += encoder_args(ffmpeg)
    cmd += ["-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE)
    assert p.stdin is not None
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    err = p.stderr.read().decode(errors="ignore") if p.stderr else ""
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {err[-900:]}")


def shot_frames(shot: dict, upto: float | None = None):
    words = shot["narration"].split()
    lines = wrap_caption(words)
    times = word_times(words, shot["vo_dur"])
    dur = shot["seconds"]
    split_t = dur * shot["split"]
    n = int(round((upto if upto is not None else dur) * FPS))
    foc = shot.get("focus", (540, 960))
    if isinstance(foc[0], (list, tuple)):
        fa, fb = tuple(foc[0]), tuple(foc[1])
    else:
        fa = fb = tuple(foc)
    for i in range(n):
        tl = i / FPS
        if tl < split_t:
            key, mv, p, fc = shot["scenes"][0], shot["moves"][0], tl / max(1e-6, split_t), fa
        else:
            key, mv = shot["scenes"][1], shot["moves"][1]
            p, fc = (tl - split_t) / max(1e-6, dur - split_t), fb
        # Redraw the art every frame: the primitives animate from the clock,
        # so characters actually move instead of sitting on a still image.
        art = A.render_scene(key, t=tl)
        img = frame(art, mv, p, fc)
        draw_caption(img, words, times, lines, tl)
        yield img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", default=str(ROOT / "sample" / "emu_storyboard.json"))
    ap.add_argument("--out", default=str(ROOT / "sample" / "emu"))
    ap.add_argument("--preview", type=int, default=0,
                    help="render N stills with captions instead of video")
    ap.add_argument("--offline", action="store_true",
                    help="reuse existing vo_*.wav and never call the TTS API")
    args = ap.parse_args()

    board = json.loads(Path(args.story).read_text(encoding="utf-8"))
    out = Path(args.out)
    audio_dir = out / "audio"
    seg_dir = out / "segments"
    audio_dir.mkdir(parents=True, exist_ok=True)
    seg_dir.mkdir(parents=True, exist_ok=True)

    print("voiceover...", flush=True)
    if args.offline:
        shots = S.prepare_shots_offline(board, audio_dir)
    else:
        shots = S.prepare_shots(board, audio_dir)
    for s in shots:
        print(f"  shot {s['id']}: vo {s['vo_dur']:.2f}s -> {s['seconds']:.2f}s  "
              f"[{s['scenes'][0]} -> {s['scenes'][1]}]", flush=True)
    total = sum(s["seconds"] for s in shots)
    print(f"total {total:.2f}s", flush=True)
    (out / "timing.json").write_text(json.dumps(shots, indent=2), encoding="utf-8")

    if args.preview:
        for s in shots[: args.preview]:
            img = list(shot_frames(s, upto=0.52 * s["seconds"]))[-1]
            img.save(out / f"preview_{s['id']:02d}.png")
            print("preview", out / f"preview_{s['id']:02d}.png", flush=True)
        return

    ffmpeg = find_ffmpeg()
    print("ffmpeg:", ffmpeg, flush=True)

    segs = []
    for s in shots:
        seg = seg_dir / f"shot_{s['id']:02d}.mp4"
        print(f"encoding shot {s['id']}...", flush=True)
        encode(ffmpeg, shot_frames(s), seg)
        segs.append(seg)

    concat = seg_dir / "concat.txt"
    concat.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in segs), encoding="utf-8")
    silent = out / "video_silent.mp4"
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-c", "copy", str(silent)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("mixing audio...", flush=True)
    mix = out / "mix.wav"
    S.mix_timed(board, shots, mix, audio_dir)

    final = out / "emu_war_short.mp4"
    subprocess.run([ffmpeg, "-y", "-i", str(silent), "-i", str(mix),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    "-shortest", str(final)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("FINAL", final, flush=True)


if __name__ == "__main__":
    main()
