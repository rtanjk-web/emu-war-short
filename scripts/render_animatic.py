#!/usr/bin/env python3
"""Render a simple stickman animatic from storyboard.json.

Outputs:
  sample/assets/shot_XX.png   - generated placeholder frames
  sample/voiceover_silent.wav - silent audio track (duration = total)
  sample/shot_XX.mp4          - per-shot video segments
  sample/animatic.mp4         - concatenated final animatic

Usage:
  python render_animatic.py ../sample/storyboard.json ../sample
"""
from __future__ import annotations
import json, math, os, shutil, subprocess, sys, textwrap, wave, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

def find_ffmpeg():
    for name in ("ffmpeg", "ffmpeg.exe"):
        p = shutil.which(name)
        if p: return p
    candidates = [
        os.environ.get("FFMPEG_BIN"),
        os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps\9.7.1.4203\ffmpeg.exe"),
    ]
    for c in candidates:
        if c and Path(c).exists(): return c
    # search CapCut Apps
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "Apps"
    if root.exists():
        for p in sorted(root.rglob("ffmpeg.exe"), reverse=True):
            return str(p)
    raise FileNotFoundError("ffmpeg not found. Set FFMPEG_BIN or install ffmpeg.")

def load_font(size):
    for name in ["arial.ttf", "Arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()

def draw_stickman(draw, cx, cy, scale=1.0, color=(20,22,26), head_r=38, pose="stand"):
    r = int(head_r * scale)
    lw = max(4, int(6 * scale))
    # head
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=lw)
    # eyes
    er = max(2, int(4*scale))
    draw.ellipse([cx-int(12*scale)-er, cy-int(8*scale)-er, cx-int(12*scale)+er, cy-int(8*scale)+er], fill=color)
    draw.ellipse([cx+int(12*scale)-er, cy-int(8*scale)-er, cx+int(12*scale)+er, cy-int(8*scale)+er], fill=color)
    # body
    body_top = cy + r
    body_bot = cy + int(140*scale)
    draw.line([cx, body_top, cx, body_bot], fill=color, width=lw)
    # arms
    arm_y = cy + int(55*scale)
    if pose == "wave":
        draw.line([cx, arm_y, cx-int(70*scale), arm_y+int(30*scale)], fill=color, width=lw)
        draw.line([cx, arm_y, cx+int(70*scale), arm_y-int(50*scale)], fill=color, width=lw)
    elif pose == "point":
        draw.line([cx, arm_y, cx-int(60*scale), arm_y+int(30*scale)], fill=color, width=lw)
        draw.line([cx, arm_y, cx+int(90*scale), arm_y-int(10*scale)], fill=color, width=lw)
    else:
        draw.line([cx, arm_y, cx-int(70*scale), arm_y+int(60*scale)], fill=color, width=lw)
        draw.line([cx, arm_y, cx+int(70*scale), arm_y+int(60*scale)], fill=color, width=lw)
    # legs
    if pose == "run":
        draw.line([cx, body_bot, cx-int(55*scale), body_bot+int(90*scale)], fill=color, width=lw)
        draw.line([cx, body_bot, cx+int(45*scale), body_bot+int(70*scale)], fill=color, width=lw)
    else:
        draw.line([cx, body_bot, cx-int(45*scale), body_bot+int(95*scale)], fill=color, width=lw)
        draw.line([cx, body_bot, cx+int(45*scale), body_bot+int(95*scale)], fill=color, width=lw)

def draw_prop(draw, kind, x, y, font):
    if "327" in kind or "dent" in kind.lower():
        draw.rectangle([x, y, x+180, y+70], outline=(255,90,54), width=5)
        draw.text((x+12, y+12), "327 DENTS", fill=(255,90,54), font=font)
    if "cup" in kind.lower() or "trophy" in kind.lower():
        draw.rectangle([x, y+20, x+80, y+80], outline=(232,192,125), width=5)
        draw.line([x+40,y+80,x+40,y+110], fill=(232,192,125), width=5)
        draw.line([x+15,y+110,x+65,y+110], fill=(232,192,125), width=5)
    if "flag" in kind.lower():
        draw.line([x, y, x, y+160], fill=(20,22,26), width=5)
        draw.polygon([(x,y),(x+70,y+30),(x,y+60)], fill=(255,90,54))

def render_shot(shot, out_png, style):
    bg = (244, 241, 234)
    ink = (20, 22, 26)
    accent = (255, 90, 54)
    blue = (44, 123, 229)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    # ground
    d.rectangle([0, 1400, W, H], fill=(230, 224, 210))
    d.line([0, 1400, W, 1400], fill=ink, width=4)
    # title/beat
    font_big = load_font(54)
    font_med = load_font(40)
    font_small = load_font(34)
    d.rectangle([60, 80, 1020, 170], outline=ink, width=4)
    d.text((80, 100), f"SHOT {shot['id']}  |  {shot['beat']}", fill=ink, font=font_big)
    # narration
    y = 210
    for line in textwrap.wrap(shot["narration"], width=34):
        d.text((80, y), line, fill=ink, font=font_med)
        y += 52
    # visual desc
    d.text((80, y+20), "Visual:", fill=blue, font=font_small)
    vy = y + 65
    for line in textwrap.wrap(shot["visual"], width=40)[:4]:
        d.text((80, vy), line, fill=(60,60,60), font=font_small)
        vy += 44
    # stickmen scene
    poses = ["stand", "point", "wave", "run", "stand", "point", "stand", "wave"]
    pose = poses[(shot["id"]-1) % len(poses)]
    draw_stickman(d, 360, 1120, scale=1.4, pose=pose)
    draw_stickman(d, 760, 1140, scale=1.3, pose="stand" if pose != "stand" else "point", color=(44,123,229))
    # props based on text
    txt = (shot["narration"] + " " + shot["visual"]).lower()
    draw_prop(d, txt, 120, 1250, font_small)
    if "flag" in txt or "hole" in txt:
        draw_prop(d, "flag", 900, 1180, font_small)
    # camera badge
    d.rectangle([720, 1750, 1020, 1830], fill=accent)
    d.text((740, 1770), f"cam: {shot['camera']}", fill=(255,255,255), font=font_small)
    # footer
    d.text((80, 1840), "FREE STICKMAN WORKFLOW PROTOTYPE", fill=(120,120,120), font=font_small)
    img.save(out_png)

def make_silent_wav(path, seconds, sr=44100):
    n = int(seconds * sr)
    with wave.open(str(path), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        # write in chunks to avoid huge memory
        chunk = struct.pack('<h', 0) * 44100
        remaining = n
        while remaining > 0:
            c = min(remaining, 44100)
            if c == 44100:
                wf.writeframes(chunk)
            else:
                wf.writeframes(struct.pack('<h', 0) * c)
            remaining -= c

def run(cmd):
    print('+', ' '.join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-1000:] if r.stdout else '')
        print(r.stderr[-1000:] if r.stderr else '')
        raise RuntimeError(f"command failed: {cmd[0]}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python render_animatic.py storyboard.json out_dir")
        sys.exit(2)
    storyboard = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2])
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg()
    print("ffmpeg:", ffmpeg)

    # 1. render frames
    for shot in storyboard["shots"]:
        png = assets / f"shot_{shot['id']:02d}.png"
        render_shot(shot, png, storyboard.get("style", ""))
        print("frame", png)

    # 2. silent audio
    total = sum(float(s["seconds"]) for s in storyboard["shots"])
    wav = out_dir / "voiceover_silent.wav"
    make_silent_wav(wav, total + 0.5)
    print("audio", wav)

    # 3. per-shot segments
    segs = []
    encoder_opts = [
        ["-c:v", "h264_mf", "-b:v", "6M"],
        ["-c:v", "h264_nvenc", "-b:v", "6M"],
        ["-c:v", "h264_qsv", "-b:v", "6M"],
        ["-c:v", "mpeg4", "-q:v", "3"],
    ]
    chosen = None
    for shot in storyboard["shots"]:
        png = assets / f"shot_{shot['id']:02d}.png"
        seg = out_dir / f"shot_{shot['id']:02d}.mp4"
        dur = float(shot["seconds"])
        opts_list = [chosen] if chosen else encoder_opts
        last_err = None
        for opts in opts_list:
            cmd = [ffmpeg, "-y", "-loop", "1", "-i", str(png), "-t", str(dur),
                   "-vf", "scale=1080:1920,format=yuv420p", "-r", str(storyboard.get("fps",30)),
                   *opts, str(seg)]
            try:
                run(cmd)
                chosen = opts
                last_err = None
                break
            except Exception as e:
                last_err = e
                if seg.exists():
                    seg.unlink()
        if last_err:
            raise last_err
        segs.append(seg)

    # 4. concat
    concat = out_dir / "concat.txt"
    concat.write_text("\n".join([f"file '{s.resolve().as_posix()}'" for s in segs]), encoding="utf-8")
    video_only = out_dir / "animatic_silent.mp4"
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(video_only)])
    final = out_dir / "animatic.mp4"
    run([ffmpeg, "-y", "-i", str(video_only), "-i", str(wav), "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)])
    print("FINAL", final)

if __name__ == "__main__":
    main()
