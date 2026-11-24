# Free Stickman Shorts Workflow Prototype

This prototype validates a **free, executable** stickman Shorts workflow inspired by `https://www.youtube.com/watch?v=M_1IGXSQX_g` ("Make Viral Stickman Shorts using FREE TOOLS..." by Caffeinated Blogger).

## What it demonstrates
1. **Research artifact** - extracted master prompt + adapted stickman prompt.
2. **Storyboard generation** - normalize a story into timed shots.
3. **Local animatic render** - generate stickman placeholder frames with Pillow and assemble a 9:16 MP4 with ffmpeg.
4. **CapCut handoff** - output can be imported into CapCut; this machine also has CapCut 9.7 and VectCutAPI MCP available for draft automation.

## Requirements
- Python 3.10+ (tested with 3.13)
- Pillow (`pip install pillow`) - already present on this machine
- ffmpeg on PATH, or `FFMPEG_BIN` set, or CapCut-bundled ffmpeg (auto-detected)

## Run
```powershell
cd C:\Users\rapha\AppData\Local\Temp\opencode\stickman-workflow
python scripts/generate_storyboard.py sample/storyboard.json sample/storyboard.normalized.json
python scripts/render_animatic.py sample/storyboard.json sample
```

Outputs:
- `sample/assets/shot_*.png` - generated frames
- `sample/voiceover_silent.wav` - silent placeholder audio
- `sample/animatic.mp4` - final 1080x1920 animatic

## Production workflow (free stack)
| Stage | Free tool | Output |
|---|---|---|
| Idea/story/script | ChatGPT free / Gemini / local LLM | narration + shot list |
| Reference image | Google Flow / Nano Banana (free credits) or local SDXL/FLUX | character/style reference |
| Shot animation | Google Flow / Pika / other free credits; or local ComfyUI/SVD for rough motion | 4-6s clips |
| Voiceover | Google AI Studio / Edge TTS / Kokoro local | WAV/MP3 |
| Captions | CapCut auto captions / Whisper | SRT |
| Edit/export | CapCut desktop | 1080x1920 30fps H.264 |

## Google AI Studio (Gemini) integration

Scripts added (REST only, no SDK install needed; uses `requests` + `Pillow` which are already installed):

| Script | Purpose |
|---|---|
| `scripts/gemini_client.py` | Auth via `GEMINI_API_KEY` env var; `models`, text generation, image generation helpers |
| `scripts/gemini_generate_story.py` | Generate an 8-shot stickman storyboard JSON with Gemini (topic as CLI arg) |
| `scripts/gemini_generate_images.py` | Generate per-shot stickman PNGs into `sample/assets/` (replaces placeholders) |

### Setup
1. Create a key at https://aistudio.google.com/apikey
2. Put it in `.env` (gitignored): `GEMINI_API_KEY=your_key_here`
3. Verify: `python scripts/gemini_client.py models`

### Usage
```powershell
python scripts/gemini_generate_story.py "a golfer who hammered 327 dents into a new ball"
python scripts/gemini_generate_images.py storyboard_gemini.json 2   # test 2 shots first
python scripts/render_animatic.py sample/storyboard_gemini.json sample
```

### Current status of the supplied key
The key pasted from the screenshot returned **HTTP 401 (invalid)** across `/models`, `/generateContent`, `/interactions` (v1 and v1beta; query param, `x-goog-api-key`, and Bearer). `.env` now contains a placeholder — insert a valid key before running the Gemini scripts. **Rotate/delete the leaked key in AI Studio** since it was shared in chat.

## Using AI Studio in the workflow
See `AI_STUDIO_WORKFLOW.md` — the web UI has its own daily quota separate from the API key, which is the key to keeping the pipeline free. Handoff scripts: **`python scripts/handoff.py --pasted pasted.json --images "C:\Users\rapha\Downloads"`** runs everything in one command (wraps `import_storyboard.py`, `map_images.py`, `render_animatic.py`).

## Video generation
See `VIDEO_SETUP.md`. Current model is `gemini-omni-1.2-flash` (Veo 3.1 is shut down). Ready-to-run scripts: `scripts/gemini_video_gen_test.py` and `scripts/gemini_image_to_video.py`. Both are blocked on this Free Tier key (0 video requests/day) until billing is enabled.

## Limitations
- The included renderer creates **placeholder animatics** unless you run the Gemini image script. AI image/video tools have credit limits, queue times, and style drift.
- Monetizable content requires original storytelling, rights-cleared assets/audio, and policy-compliant reuse.
