#!/usr/bin/env python3
"""Convert ai4bharat/IndicF5 model.safetensors into a checkpoint F5-TTS's Trainer can load.

IndicF5 stores 364 DiT tensors under `ema_model._orig_mod.transformer.*` plus 83 bundled
Vocos tensors under `vocoder._orig_mod.*`. The upstream Trainer loads a `.safetensors`
pretrain as {"ema_model_state_dict": <file>} and calls EMA.load_state_dict strictly, so the
file must contain `ema_model.transformer.*` + `initted` + `step` and nothing else.

Usage:
    python 02_convert_indicf5_ckpt.py --out /abs/path/pretrained_indicf5_base.safetensors
Downloads model.safetensors + checkpoints/vocab.txt from HF (needs an accepted gate + token).
"""
import argparse
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file, save_file

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default="ai4bharat/IndicF5")
ap.add_argument("--out", required=True)
ap.add_argument("--vocab-out", default=None, help="where to also copy checkpoints/vocab.txt")
args = ap.parse_args()

src = hf_hub_download(args.repo, "model.safetensors")
vocab = hf_hub_download(args.repo, "checkpoints/vocab.txt")
sd = load_file(src)
out, dropped = {}, 0
for k, v in sd.items():
    if k.startswith("vocoder."):
        dropped += 1
        continue
    pre = "ema_model._orig_mod."
    assert k.startswith(pre), f"unexpected key {k}"
    out["ema_model." + k[len(pre):]] = v
out["initted"] = torch.tensor(True)
out["step"] = torch.tensor(0)

emb = out["ema_model.transformer.text_embed.text_embed.weight"]
n_vocab = sum(1 for _ in open(vocab, encoding="utf-8"))
print(f"kept {len(out)-2} transformer tensors, dropped {dropped} vocoder tensors")
print(f"text_embed shape {tuple(emb.shape)}; vocab lines {n_vocab} (expect embedding rows = vocab+1)")
assert len(out) - 2 == 364, len(out) - 2
assert emb.shape[0] == n_vocab + 1, (emb.shape, n_vocab)

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
save_file(out, args.out)
print("wrote", args.out)
if args.vocab_out:
    Path(args.vocab_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.vocab_out).write_bytes(Path(vocab).read_bytes())
    print("wrote", args.vocab_out)
