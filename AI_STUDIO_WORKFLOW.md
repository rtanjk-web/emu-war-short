# Using Google AI Studio in the stickman Shorts workflow

Source: https://aistudio.google.com/docs/google-ai-plans.md, /docs/rate-limits.md, /docs/billing.md (checked 2026-11-23)

## The key distinction

| Surface | Auth | Quota | What it's good for |
|---|---|---|---|
| **AI Studio web UI** (Playground / Build) | Your Google sign-in | Its own **subscription daily quota** (Free = modest); resets daily, separate from API key | Creative work: scripting, reference images, voiceover, one-off video clips — manual download |
| **Gemini API key** (our `google-genai` scripts) | `GEMINI_API_KEY` | Per project/usage tier: `gemini-4-hydrogen` 20 RPD on Free; **0 RPD for image and video models** | Automation, batching, reproducible scripts |
| **Paid API key** (billing / Google AI Pro credits) | Same key, linked billing | Tier 1+: Omni video 40 RPD, higher text limits; Pro plan includes $10/mo Cloud credits for the API | Full automated pipeline |

Important: subscription quota applies **only inside the AI Studio web interface**. Claimed Cloud credits apply to API requests with a paid key. RPD resets at **midnight Pacific time**.

## Free, no-billing workflow (recommended)

| Stage | Use | How |
|---|---|---|
| 1. Idea + script | **AI Studio Playground (browser)** | New chat → paste `prompts/stickman_adaptation_prompt.txt` or `prompts/gemini_story_prompt.txt`. Ask for the 8-shot JSON schema. Copy output to `sample/storyboard.json` |
| 2. Reference image + shot images | **AI Studio image generation (browser)** | Generate the character line-up, then one image per shot; download into `sample/assets/shot_01.png` … `shot_08.png` |
| 3. Voiceover | **AI Studio speech generation (browser)** or local Kokoro/Edge TTS | Download WAV to `sample/voiceover.wav` |
| 4. Captions | CapCut auto-captions | Import audio, generate captions, style them |
| 5. Assembly | **Local scripts (no quota)** | `python scripts/render_animatic.py sample/storyboard.json sample` → 1080x1920 MP4 via Pillow + CapCut ffmpeg |
| 6. Final edit | CapCut desktop | zooms, transitions, SFX, music, export 1080x1920/30fps |

## Handoff scripts (paste from browser -> render locally)

**Single command** (runs all three steps in sequence, stops on failure):
```powershell
python scripts/handoff.py --pasted pasted.json --images "C:\Users\rapha\Downloads"
# -> <out>/animatic.mp4  (default out folder: sample/)
```
Options: `--out DIR`, `--count N`, `--no-crop`, `--skip-render` (prepare JSON/assets only).

Individual steps (what the wrapper runs):

1. Save the Playground storyboard JSON to a file (or pipe it via stdin), then validate/normalize it:
   ```powershell
   python scripts/import_storyboard.py pasted.json --out sample/storyboard.json
   ```
   Hard errors (bad JSON, no shots, no narration) stop the import; soft issues (hook length, word count, beat order, repeated camera) print warnings but still produce a renderable file. Markdown fences around pasted JSON are stripped automatically.

2. Download the generated images from AI Studio into one folder, then map them into the renderer's filenames:
   ```powershell
   python scripts/map_images.py --src "C:\Users\rapha\Downloads"
   ```
   Filenames containing `shot 3`, `shot_03`, `frame-2` or a bare `3` are matched to that shot number; leftovers fill remaining slots in modification-time order. Images are converted to PNG and centre-cropped to 1080x1920. Use `--no-crop` to keep the source aspect ratio. Missing slots are reported and existing files are left untouched.

3. Render:
   ```powershell
   python scripts/render_animatic.py sample/storyboard.json sample
   ```

Notes:
- The API text model is capped at 20 requests/day on this key — use it for one automated storyboard per day at most, or after midnight Pacific.
- `gemini-omni-1.2-flash` (video) and all image models return 429 with 0 quota on this API key — generate those in the **web UI**, not through scripts.
- Agents (Antigravity / Deep Research) are documented as requiring a paid key, although a test Antigravity call succeeded once on this key; do not rely on it.

## If you enable billing (or have Google AI Pro)

1. In AI Studio: **Claim free API credits** or **Set up billing** for the project. Pro = $10/mo, Ultra = $40-100/mo in API credits. Prepay requires a $5 minimum purchase.
2. Link the paid key in AI Studio (key icon in Playground; `GEMINI_API_KEY` in Build → Secrets).
3. Then the ready scripts work unchanged:
   - `scripts/gemini_generate_story.py` / structured output → validated storyboard JSON
   - `scripts/gemini_generate_images.py` → Nano Banana shot images
   - `scripts/gemini_video_gen_test.py` and `scripts/gemini_image_to_video.py` → Omni 1.2 Flash 9:16 clips
   - `scripts/gemini_multimodal_test.py` → fact-checking with Google Search grounding (add `tools=[{"type":"google_search"}]`)
4. Set a monthly spend cap at https://aistudio.google.com/spend before scaling.

## Why this split matters for the original objective

A fully automated, *free* API pipeline is not viable here: image/video models have zero free API quota and text is 20 RPD. The viable free model is **hybrid**: AI Studio web UI for generative assets (its own quota) + local Python/CapCut for deterministic assembly. That is still "free tools", just not a single scripted API call.
