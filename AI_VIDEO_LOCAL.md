# Free local AI video (option C)

Google's hosted image/video models have **zero free-tier quota** on this account, so the
only genuinely unlimited AI-video route is an open-weight model on your own GPU. This
machine has an RTX 2080 Ti (11 GB), which is enough for **LTX-Video 0.9.5 (2B)**.

## Measured result

| Metric | Value |
|---|---|
| Model | `Lightricks/LTX-Video-0.9.5` (diffusers `LTXPipeline`) |
| Output | 512x896, 49 frames, 24 fps, 2.04 s |
| Steps | 30 (~1 s/step) |
| **Generation time** | **26.8-30.9 s** (after model load, two runs) |
| Model load / text encode | ~38-50 s cached / cold; T5 ~11-13 s |
| **Peak VRAM** | **7.15 GiB** (fits an 11 GB card with room to spare) |
| Output size | 106 KB, 419 kb/s H.264 |
| Cost | $0, no quota, no API key |

Sanity checks on the generated clip: non-static (mean frame-to-frame delta 12-13
levels), good contrast (std 83/255), 4,299 distinct colours in a subsample — not a
blank or frozen output. Preview it at
`C:\Users\rapha\AppData\Local\Temp\opencode\vidgen\out\emu_ltx.mp4`.

Setup on this machine:

```powershell
$v = "$env:TEMP\opencode\vidgen\venv"
python -m venv $v
& "$v\Scripts\pip.exe" install torch --index-url https://download.pytorch.org/whl/cu126
& "$v\Scripts\pip.exe" install diffusers transformers accelerate sentencepiece protobuf imageio imageio-ffmpeg ftfy safetensors
```

Render a clip:

```powershell
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
& "$v\Scripts\python.exe" extras/ltx_video.py `
  "Cinematic close-up of an emu in golden hour light, dusty wheat field, slow push-in" `
  out/emu_broll.mp4 512 896 49 30
```

Args after the output path are `width height frames steps`.

## Why the script looks the way it does

- T5-XXL is moved to **CPU in fp32**: at fp16 it would consume ~9.5 GB by itself and
  leave no room for the transformer.
- The prompt is encoded with `pipe.encode_prompt(..., device=cpu)` **before** the
  diffusion call, and the resulting embeddings are passed to `pipe(...)`. Without
  this, the pipeline moves `input_ids` to CUDA while T5's weights are on CPU and
  raises a device-mismatch error.
- `vae.enable_tiling()` keeps VAE decoding inside 8 GB.

## Verdict

Use it for **short AI b-roll inserts** (2 s each) where motion or photorealism
sells a beat — a slow push-in on an emu, dust, a machine-gun close-up. It is
not a replacement for the stickman renderer: cuts must still land exactly on the
narration, and the flat-vector style is what makes each beat readable at phone
size. Generating ~16 bespoke clips would take roughly 8-10 minutes of GPU time plus
manual prompt work, versus ~2.5 minutes for a full deterministic CPU render.

Keep the two pipelines separate: `scripts/make_short.py` owns the master timeline;
drop any generated MP4 in as an optional segment rather than re-rendering the story
through a diffusion model.
