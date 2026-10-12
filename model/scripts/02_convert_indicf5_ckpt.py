#!/usr/bin/env python3
"""Convert ai4bharat/IndicF5 model.safetensors into a checkpoint that F5-TTS's Trainer can load.

IndicF5 stores 364 DiT tensors under `ema_model._orig_mod.transformer.*` plus 83 bundled
Vocos tensors under `vocoder._orig_mod.*`. The F5-TTS Trainer loads a `.safetensors`
pretrain as {"ema_model_state_dict": <file>} and calls EMA.load_state_dict strictly, so the
file must contain `ema_model.transformer.*` + `initted` + `step` and nothing else.

Usage:
    python 02_convert_indicf5_ckpt.py --out /abs/path/pretrained_indicf5_base.safetensors
Downloads model.safetensors + checkpoints/vocab.txt from Hugging Face (needs an accepted gate + token).
"""
import argparse
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
from safetensors.torch import save_file

PREFIX = "ema_model._orig_mod."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="ai4bharat/IndicF5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vocab-out", default=None, help="where to also copy checkpoints/vocab.txt")
    args = ap.parse_args()

    model_path = hf_hub_download(args.repo, "model.safetensors")
    vocab_path = hf_hub_download(args.repo, "checkpoints/vocab.txt")
    tensors = load_file(model_path)

    converted = {}
    dropped = 0
    for key, value in tensors.items():
        if key.startswith("vocoder."):
            dropped += 1
            continue
        assert key.startswith(PREFIX), f"unexpected key {key}"
        converted["ema_model." + key[len(PREFIX):]] = value
    converted["initted"] = torch.tensor(True)
    converted["step"] = torch.tensor(0)

    n_transformer = len(converted) - 2
    embedding = converted["ema_model.transformer.text_embed.text_embed.weight"]
    with open(vocab_path, encoding="utf-8") as f:
        n_vocab = len(f.readlines())
    print(f"kept {n_transformer} transformer tensors, dropped {dropped} vocoder tensors")
    print(f"text_embed shape {tuple(embedding.shape)}; vocab lines {n_vocab} (expect embedding rows = vocab+1)")
    assert n_transformer == 364, n_transformer
    assert embedding.shape[0] == n_vocab + 1, (embedding.shape, n_vocab)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_file(converted, args.out)
    print("wrote", args.out)
    if args.vocab_out:
        Path(args.vocab_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.vocab_out).write_bytes(Path(vocab_path).read_bytes())
        print("wrote", args.vocab_out)


if __name__ == "__main__":
    main()
