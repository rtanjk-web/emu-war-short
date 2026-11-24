# Free Stickman Shorts Workflow - Research, Prototype, Assessment

## Objective
Research and validate free stickman-animated Shorts workflows starting from `https://www.youtube.com/watch?v=M_1IGXSQX_g`, prototype an executable workflow, and assess whether it can produce genuinely entertaining, monetizable content.

## 1) Reference video findings

**Video**: "Make Viral Stickman Shorts using FREE TOOLS (NO CLAUDE CODE) like Ricks Clips"  
**Channel**: Caffeinated Blogger  
**Published**: 2026-11-18 (from metadata) | **Views**: 168,602 | **Likes**: 4,493 | **Duration**: 693s

**Claimed workflow (from description/transcript/prompt doc):**
1. **ChatGPT (free)** + master prompt generates story, style sheet, reference-image prompt, and per-shot video prompts.
2. **Reference screenshots** from target style are fed to ChatGPT to match look.
3. **Google Flow / Nano Banana** (free credits) generates 9:16 reference image and shot animations.
4. **Google AI Studio** generates free voiceover.
5. **CapCut** edits, captions, zooms/transitions, exports.

**Key prompt strategy** (`prompts/master_prompt_ricks_clips_v3.txt`, extracted from public doc linked in description):
- Forces true-story "hidden-physics underdog" beats (hook, setup, doubt, escalate, turn, reveal, button).
- One sentence = one shot = 4-6s = one clear camera/action.
- Character consistency via fixed character sentences + reference image attached to every shot.
- No captions/logos/watermarks in generated frames; captions added in edit.

**Important nuance**: the referenced "Ricks Clips" style is **flat 2D cartoon characters on stylized 3D backgrounds**, not pure stick figures. The workflow is adjacent to stickman content and can be adapted to true stickman style by changing the style sheet.

## 2) Free workflow map (validated)

| Stage | Free option | Validation | Main risk |
|---|---|---|---|
| Research/idea | ChatGPT/Gemini free, manual research | Viable | factual errors, generic ideas |
| Script/storyboard | ChatGPT/Gemini with structured prompt | Viable; prompt enforces beats | hallucinated "true facts", weak hooks |
| Reference image | Google Flow/Nano Banana free credits, Bing Image Creator, local SDXL/FLUX | Viable but credit-limited | style drift, character inconsistency |
| Shot animation | Google Flow/Veo/Pika/Kling free tiers; local SVD/Wan (low-res) | Partially viable | credits, queue, morphing, low fidelity |
| Voiceover | Google AI Studio, Edge TTS, Kokoro local | Viable | robotic pacing, licensing/terms |
| Captions | CapCut auto captions, Whisper | Viable | timing cleanup needed |
| Edit/assembly | CapCut desktop (installed locally) | Viable; CapCut 9.7 + ffmpeg present | manual polish time |
| Local animatic fallback | Python + Pillow + ffmpeg | **Executable now** (prototype) | not "animated" enough for high retention |

## 3) Prototype (executable)

Location: `C:\Users\rapha\AppData\Local\Temp\opencode\stickman-workflow`

### Files
- `prompts/master_prompt_ricks_clips_v3.txt` - extracted reference prompt.
- `prompts/stickman_adaptation_prompt.txt` - stickman-specific adaptation.
- `scripts/generate_storyboard.py` - normalizes story input into timed shot plan.
- `scripts/render_animatic.py` - generates stickman placeholder frames and assembles 1080x1920 MP4 via ffmpeg.
- `sample/storyboard.json` - sample "hidden-physics underdog" story.
- `sample/storyboard.normalized.json` - generated normalized plan.
- `sample/animatic.mp4` - rendered prototype output.

### Commands run
```powershell
python scripts/generate_storyboard.py sample/storyboard.json sample/storyboard.normalized.json
python scripts/render_animatic.py sample/storyboard.json sample
```

### Observed result
- Storyboard normalized: **8 shots, 32.0s, 108 words**.
- Animatic rendered: **sample/animatic.mp4**, ~6.4MB, **1080x1920, 30fps, H.264, ~32s**, silent AAC audio.
- ffmpeg used: CapCut-bundled `C:\Users\rapha\AppData\Local\CapCut\Apps\9.7.1.4203\ffmpeg.exe` with `h264_mf` encoder fallback.

### What the prototype proves
- The workflow skeleton is executable locally with free tools already present.
- Storyboard normalization, asset generation, and vertical video assembly can be automated.
- CapCut can be the final editor; this machine also has VectCutAPI/CapCut MCP for draft automation.

### What it does not prove
- It does **not** prove AI-generated shot quality/consistency at scale. The renderer produces static placeholder stickman frames, not the high-motion 2D/3D hybrid look in the reference video.

## 4) Entertainment & monetization assessment

## Can it produce entertaining content?
**Potentially yes, but tooling is not the differentiator.** The reference prompt encodes good retention mechanics: fast hook, visible stakes, ridicule, escalation, payoff, concrete numbers/props. These are story devices, not AI features. A free workflow can produce entertaining Shorts if:
- Hook lands in first 1-2 seconds.
- Each shot shows a clear visual change matching narration.
- Story has a real, surprising, verifiable fact.
- Captions, pacing, sound effects, and music are tightly edited.

**Failure modes**: generic AI look, character drift, morphing limbs, repetitive motion, fake/unclear facts, slow narration, no payoff.

## Can it produce monetizable content?
**Technically possible, but not guaranteed and not "easy money".** Considerations:
- **YouTube Shorts monetization** depends on eligibility (YPP thresholds/policies), RPM variability, and advertiser suitability; Shorts RPM is typically much lower than long-form. The video's "$92k" claim is a rough back-of-envelope estimate, not a guarantee.
- **Policy/originality risk**: mass-produced, templated, low-differentiation AI content can be limited by YouTube's reused/repetitious content and spam policies. Original narration, fact-checking, editing, and transformative value matter.
- **Rights/terms**: verify commercial terms for each AI tool (image/video/voice/music), avoid copyrighted characters/music, and disclose synthetic content where required.
- **Cost**: "free" usually means limited credits/time. Scaling beyond occasional posts often pushes to paid tiers or significant manual labor.

## Verdict
- **Workflow validity**: **Validated** as a feasible free/prototyping pipeline.
- **Executable prototype**: **Completed** (local storyboard + animatic render).
- **Entertaining at scale**: **Unproven**; depends on story craft and shot quality.
- **Reliable monetization**: **Unproven/high variance**; possible only with original, policy-compliant, high-retention execution.

## 4b) Google AI Studio (Gemini) API integration

Added to the prototype:
- `scripts/gemini_client.py` - env-var based REST client (models / text / image).
- `scripts/gemini_generate_story.py` - generates the 8-shot stickman storyboard with Gemini.
- `scripts/gemini_generate_images.py` - generates per-shot stickman PNGs to replace placeholders.
- `prompts/gemini_story_prompt.txt` - non-interactive prompt enforcing the retention beat structure and JSON schema.
- `.env` (gitignored) + `.gitignore` for secure key handling.

**Validation status: BLOCKED at auth.** The API key supplied by screenshot was tested against:
- `GET /v1beta/models` and `/v1/models` with `?key=`, `x-goog-api-key`, and `Authorization: Bearer`
- `POST /v1beta/models/gemini-2.5-flash:generateContent`
- `POST /v1beta/interactions` (2026 revision) with `gemini-4-hydrogen` and `gemini-2.5-flash`

All returned **HTTP 401 - "API key not valid"**. The key is therefore invalid, revoked, or mistyped in the screenshot. `.env` now holds a placeholder; drop a fresh key from https://aistudio.google.com/apikey into it to activate the scripts. The key shared in chat should be **revoked/rotated** regardless.

## 4c) Free-tier quota findings (tested 2026-11-23)

Live testing with the official `google-genai` SDK and Interactions API established:

| Model / capability | Free-tier result |
|---|---|
| `gemini-4-hydrogen` (text, streaming, multimodal, structured output) | Works, but **20 requests/day** quota. Exhausted during this session's tests; API reported "retry in 20h51m" |
| `antigravity-preview-09-2026` managed agent (`environment="remote"`) | **Works on free tier** with separate quota, but long-running (minutes); a blocking `interactions.create` call needed a multi-minute wait. Ideal candidate for background execution/polling |
| `gemini-3.1-flash-image`, `gemini-2.5-flash-image` | **429 — 0 input tokens/minute** |
| `gemini-nano-banana-2.1`, `gemini-3-pro-image`, `gemini-3.1-flash-lite-image` | **429 — 0 requests/day** |

Important behavior: the Python SDK **silently retries 429/503 errors**, so a rate-limited call appears to hang for minutes rather than failing fast. Raw REST (`POST /v1beta/interactions` with `x-goog-api-key` and `Api-Revision: 2026-05-20`) returns the real error in ~0.2s and is the reliable way to diagnose quota issues.

Implication for the original objective: an API-based "free" image-generation Shorts workflow is **not viable on this free tier** — image models have zero quota and text is capped at 20 requests/day. Viable free alternatives: Google AI Studio web UI credits, local image/voice generation (ComfyUI/SDXL/FLUX, Kokoro), or enabling billing.

## 5) Recommended next steps
1. **Replace placeholders with real shots**: use the adapted prompt to generate reference + 8 shot clips; keep character reference fixed.
2. **Add real voiceover**: Google AI Studio or local Kokoro/Edge TTS; target 140-160 wpm for 30s.
3. **Edit in CapCut**: auto captions, punch-in zooms on reveals, SFX on impacts, fast cuts; export 1080x1920/30fps.
4. **Fact-check** every claim before publishing; put true fact in description.
5. **A/B test hooks**: produce 5 variants of same story hook; keep retention analytics, not view-count anecdotes.
6. **Compliance gate**: check tool ToS, music rights, AI disclosure, and YouTube originality policies before scaling.
