# Free cloud render (GitHub Actions)

The renderer is CPU-only (Pillow + ffmpeg), so a standard GitHub-hosted Linux
runner renders this 35 s short in ~2-3 minutes at zero cost.

## What makes it work in CI

| Local | Cloud |
|---|---|
| CapCut ffmpeg, `h264_mf` | Ubuntu ffmpeg, `libx264` |
| `.env` + TTS API | committed `vo_*.wav`, `--offline` |
| Arial / Segoe | DejaVu Sans (already in the font fallback chain) |

`make_short.py` probes `ffmpeg -encoders` and picks `h264_mf`, `libx264`, or
plain `h264` in that order. `--offline` builds the timeline from the existing
voice files and never calls the TTS API, so no key and no quota are needed.

## One-time setup

```powershell
cd C:\Users\rapha\AppData\Local\Temp\opencode\stickman-workflow

git init
git add .
git commit -m "Emu War short: renderer, art, voice, CI"

# create an empty PUBLIC repo on github.com first (no README), then:
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Before pushing, confirm the key is not staged:

```powershell
git status --short | Select-String ".env"
```

`.env` is in `.gitignore`; the scripts only read the key from the environment.

## Render

- **Actions → render-short → Run workflow**, or push any change to
  `scripts/`, `sample/`, or the workflow file.
- When the job finishes, download **emu-war-short** from the run's Artifacts.

## Changing the video

```powershell
# 1. edit sample/emu_storyboard.json (narration / scenes / focus)
# 2. regenerate voice locally (needs GEMINI_API_KEY in .env)
python scripts/make_short.py --story sample/emu_storyboard.json --out sample/emu --preview 8
# 3. commit the new sample/emu/audio/vo_*.wav, push
```

CI only re-renders pictures, captions and the mix; it never re-records voice.

## Limits

- Public repo: standard runners are free and unmetered.
- Private repo: GitHub Free includes $12/month of compute (~2,000 Linux
  minutes), so ~300 renders/month.
- 6 h per job, 500 MB artifact storage per repo (the MP4 is ~35 MB).
- Public means the storyboard, art and narration are visible. Do not commit
  `.env`, brand assets you don't own, or client footage.
