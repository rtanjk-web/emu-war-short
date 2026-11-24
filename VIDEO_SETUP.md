# Video generation setup (checked against https://aistudio.google.com/docs on 2026-11-23)

## Current model
`gemini-omni-1.2-flash` — Gemini Omni 1.2 Flash. This is the current video-generation model in the Gemini API.

- **Veo 3.1 Preview is shut down** (Oct 22, 2026): `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview`. Do not use them.
- `gemini-omni-1.1-flash` remains in a transition window until Dec 3, 2026, then auto-routes to 1.2.
- `genie-4` is for real-time interactive world generation, not Shorts clips (returned 400 for a simple text-to-video payload).

## API shape (Interactions API, `google-genai` SDK)
```python
from google import genai
client = genai.Client()
r = client.interactions.create(
    model="gemini-omni-1.2-flash",
    input="...",                       # string, or list of image/text content blocks
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",        # "9:16" or "16:9" (default 16:9)
        "duration": "4s",              # 3s-15s, default 10s
        "resolution": "720p",          # 360p / 720p / 1080p / 4k
    },
)
open("clip.mp4", "wb").write(__import__("base64").b64decode(r.output_video.data))
```

- `output_video` is an **SDK-only** convenience field. Over REST, read the base64 video from `steps[].content[]` where `type == "video"`.
- Text-to-video: plain string input.
- Image-to-video: `input=[{"type":"image","data":<b64>,"mime_type":"image/png"}, {"type":"text","text":"..."}]`.
- Up to **6 reference images** per request for character consistency (3 per character, 2 characters).
- First/last frame interpolation and extension: 3-10s; single-image generation up to 15s.
- Don't use deprecated control tags like `<FIRST_FRAME>`; describe roles in natural language.

## Scripts ready to run
| Script | Purpose |
|---|---|
| `scripts/gemini_video_gen_test.py` | Text-to-video, 9:16, 4s, 720p |
| `scripts/gemini_image_to_video.py` | Animate a local stickman frame (`sample/assets/shot_01.png`) |

## Blocker on this key (verified via raw REST, 2026-11-23)
```
HTTP 429 — Rate limit exceeded for model gemini-omni-1.2-flash
(limit: 0 requests per day on Free Tier). Please upgrade your tier at
https://ai.dev/rate-limit.
```
`gemini-omni-1.1-flash` is also 0 requests/day. **Video generation requires billing on this account.** The scripts above are correct and will run unchanged once billing is enabled.

## Free alternatives for the stickman workflow
- Google AI Studio **web UI** may offer separate generation credits.
- Local generation already in this project: `sample/assets/shot_*.png` frames + `scripts/render_animatic.py` (Pillow + CapCut-bundled ffmpeg) produces a 1080x1920 animatic with zero API quota.
