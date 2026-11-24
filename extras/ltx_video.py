"""Free local AI video: LTX-Video 0.9.5 (2B) on a 10 GB GPU.

Text encoder runs on CPU in fp32 (T5-XXL is ~9.5 GB fp16 and would not fit
alongside the transformer), transformer + VAE stay on the GPU.

Usage:
  python gen.py "prompt" out.mp4 [width height frames steps]
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
from diffusers import LTXPipeline
from diffusers.utils import export_to_video

MODEL = "Lightricks/LTX-Video-0.9.5"


def main() -> None:
    prompt = sys.argv[1]
    out = sys.argv[2]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 512
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 896
    frames = int(sys.argv[5]) if len(sys.argv) > 5 else 49
    steps = int(sys.argv[6]) if len(sys.argv) > 6 else 30

    print(f"loading {MODEL} ...", flush=True)
    t0 = time.time()
    pipe = LTXPipeline.from_pretrained(MODEL, torch_dtype=torch.float16)
    pipe.text_encoder.to("cpu", dtype=torch.float32)
    pipe.transformer.to("cuda")
    pipe.vae.to("cuda")
    pipe.vae.enable_tiling()
    print(f"loaded in {time.time() - t0:.1f}s", flush=True)
    print(f"vram allocated: {torch.cuda.memory_allocated() / 2**30:.2f} GiB", flush=True)

    # T5 lives on CPU, so encode here and hand the pipeline finished embeddings;
    # otherwise it sends input_ids to the GPU and T5's weights are elsewhere.
    t_enc = time.time()
    emb, mask, neg_emb, neg_mask = pipe.encode_prompt(
        prompt=prompt,
        negative_prompt="blurry, low quality, watermark, text, distorted",
        device=torch.device("cpu"),
    )
    emb = emb.to("cuda", torch.float16)
    mask = mask.to("cuda")
    neg_emb = neg_emb.to("cuda", torch.float16)
    neg_mask = neg_mask.to("cuda")
    print(f"text encoded in {time.time() - t_enc:.1f}s", flush=True)

    t1 = time.time()
    result = pipe(
        prompt_embeds=emb,
        prompt_attention_mask=mask,
        negative_prompt_embeds=neg_emb,
        negative_prompt_attention_mask=neg_mask,
        width=width,
        height=height,
        num_frames=frames,
        num_inference_steps=steps,
        guidance_scale=3.0,
    )
    gen = time.time() - t1
    print(f"generated in {gen:.1f}s ({gen / steps:.2f}s/step)", flush=True)
    print(f"peak vram: {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB", flush=True)

    export_to_video(result.frames[0], out, fps=24)
    print("wrote", out, flush=True)

if __name__ == "__main__":
    main()
