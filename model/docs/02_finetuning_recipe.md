# 02 — Fine-tuning recipe v1 (IndicF5 → Hinglish on 4×A16)

Verified 2026-09-28 against `SWivid/F5-TTS` main (`2832525`, v1.1.22), the IndicF5 GitHub/HF repos, the NVIDIA A16 product brief, and three public IndicF5 fine-tunes (Orato, Saravananravi, ehzawad). Items marked ⚠ are extrapolated.

## 2.1 Hardware reality: NVIDIA A16

| Fact | Value | Consequence |
|---|---|---|
| One board = 4 GPUs (GA107, Ampere, sm_86) | 16 GB **each**, not pooled | DDP with 4 replicas; each rank must fit model + optimizer in 16 GB |
| FP32 / FP16-tensor per GPU | 4.5 / 17.9 TFLOPS | ~1/6–1/8 of an RTX 3090, ~1/17 of an A100 per GPU |
| Memory bandwidth per GPU | 200 GB/s | 1/4 of a 3090 |
| Interconnect | PCIe Gen4 via on-board switch, **no NVLink** | All-reduce of ~1.35 GB grads per update costs 0.1–0.3 s |
| BF16 | supported on Ampere ⚠ (not in datasheet tables) | fp16 or bf16 both usable |

Net: **4×A16 ≈ half a 3090.** Fine. Use mixed precision; fp32 would be 3–4× slower.

## 2.2 Facts about the training stack that shape the recipe

- `finetune_cli.py` args (verbatim defaults): `--exp_name F5TTS_v1_Base` (choices `F5TTS_v1_Base|F5TTS_Base|E2TTS_Base`), `--learning_rate 1e-5`, `--batch_size_per_gpu 3200`, `--batch_size_type frame`, `--max_samples 64`, `--grad_accumulation_steps 1`, `--max_grad_norm 1.0`, `--epochs 100`, `--num_warmup_updates 20000`, `--save_per_updates 50000`, `--keep_last_n_checkpoints -1`, `--last_per_updates 5000`, `--finetune`, `--pretrain PATH`, `--tokenizer pinyin|char|custom`, `--tokenizer_path`, `--log_samples`, `--logger wandb|tensorboard`, `--bnb_optimizer`.
- **IndicF5 = `F5TTS_Base` (v0 arch)**: DiT dim 1024, depth 22, heads 16, ff_mult 2, text_dim 512, conv_layers 4, `text_mask_padding=False`, `pe_attn_head=1`. Vocab 2545 entries, embedding `[2546, 512]`. Use `--exp_name F5TTS_Base`, **not** v1.
- **IndicF5 checkpoint layout**: `model.safetensors` has 447 tensors: 364 `ema_model._orig_mod.transformer.*` + 83 `vocoder._orig_mod.*` (bundled Vocos). Trainer expects `ema_model.transformer.*` + `initted` + `step`. → convert with `02_convert_indicf5_ckpt.py`.
- **Vocab**: `checkpoints/vocab.txt`, 2545 lines, index 0 = space, contains a–z, A–Z, digits, Devanagari, punctuation. HiACC's 118 distinct chars are all covered (checked). Pass `--tokenizer custom --tokenizer_path <vocab>`; dataset dir must be `data/<name>_custom/`.
- `prepare_csv_wavs.py`: CSV header `audio_file|text`, absolute paths. Writes `raw.arrow`, `duration.json`, and **copies the Emilia pinyin vocab** as `vocab.txt` unless `--pretrain` is passed (inverted semantics). Overwrite with IndicF5's vocab after running it.
- Dataset filter: clips outside 0.3–30 s skipped; resampled on the fly to 24 kHz (we pre-resample anyway). Any clip longer than `batch_size_per_gpu` frames is silently dropped (20 s = 1,875 frames, fine).
- Mixed precision is **only** set via accelerate (`--mixed_precision fp16|bf16|no`), not a CLI flag.
- EMA is always on (beta 0.9999, update_every 10). In a ~2k-update run EMA ≈ pretrained weights. Evaluate `model_last.pt` with `use_ema=False` first (raw weights); ehzawad shipped raw for this reason.
- Warmup: `--num_warmup_updates N` is multiplied by num_processes internally; pass the real number.
- Checkpoints: `ckpts/<dataset_name>/model_last.pt` every `last_per_updates`; `model_<n>.pt` every `save_per_updates`.

## 2.3 NaN / precision evidence

- Maintainer (issue #832): very short clips give "poisonous loss values under bf16"; "we always train with fp16"; filter dirty pairs and clips <3 s with ASR.
- Orato (IndicF5, 194 h): bf16 NaN'd mid-run → fp32. ehzawad (IndicF5, 16 h): bf16 autocast stable for 2.5k updates. #867: bf16 fine for 195k steps on v1.
- **HiACC risk:** median clip 3.0 s; 40% of clips are under 3 s. Mitigation ladder: (1) `--min-sec 1.0`, fp16; (2) merge consecutive same-speaker segments to ≥4 s (`--merge-to-sec 4` in the prep script, train split only); (3) fp32 fallback.

## 2.4 VRAM

- ehzawad measured **6.1 GiB peak at 8,192 frames/GPU** with bf16 autocast + 8-bit Adam on IndicF5. fp32 AdamW adds ~2 GB → ~8 GiB.
- Gradio heuristic for 16 GB: 5,632 frames (conservative).
- **Start at 8,192 frames, `--max_samples 32`.** Raise to 12,800 if peak < 11 GiB. Add `--bnb_optimizer` if a rank OOMs.

## 2.5 Hyperparameters v1

| Knob | Value | Why |
|---|---|---|
| exp_name | `F5TTS_Base` | IndicF5 architecture |
| tokenizer | `custom` + IndicF5 vocab | Latin + Devanagari already covered |
| pretrain | converted IndicF5 (`pretrained_indicf5_base.safetensors`) | |
| precision | fp16 (accelerate) | maintainer recommendation; bf16 second; fp32 fallback |
| lr | **2e-5** | between Orato/Saravananravi 1e-5 (large data) and ehzawad 3e-5 (16 h); drop to 1e-5 if val CER worsens by 500 updates |
| batch | 8,192 frames/GPU × 4 = 32,768 frames/update (~350 s audio) | VRAM-safe |
| grad accum | 1 | |
| epochs | 60 (~33 updates/epoch on 2.2 h → ~2,000 updates) | ehzawad converged at 2.5k |
| warmup | 100 | small-data practice |
| save | every 250 updates, keep last 5, `model_last` every 50 | evaluate every 250 |
| EMA | on (automatic); evaluate raw first | see 2.2 |
| max_grad_norm | 1.0 | default |
| data | HiACC adult train, mixed clips ×2, ≥1.0 s | see 01 |
| logger | tensorboard | no wandb account needed |

Wall-clock ⚠: ehzawad got ~6,100 frames/s on one RTX A5000. A16 per GPU ≈ 1/6 → ~1,000–1,500 frames/s; 4 GPUs minus PCIe overhead ≈ 3,000–4,500 frames/s. 2.2 h data ≈ 950 k frames/epoch → **4–6 min/epoch → 60 epochs ≈ 4–6 h** in fp16. fp32 ≈ 15–24 h.

## 2.6 Planned ablations (after v1 runs clean)

1. Clean-Hindi mixing (1–2 h IndicVoices-R Hindi, gated CC BY) at 1:1 — protects base quality, adds wideband audio.
2. Mixed-only vs all-adult clips.
3. Merge-to-4s vs raw segments.
4. lr 1e-5 vs 2e-5.
5. LoRA (instavar fork, r=16, `to_q to_k to_v to_out.0 ff.ff.0.0 ff.ff.2`, lr 1e-4) vs full — cheaper, unbenchmarked.
6. Adult + children.

## 2.7 Alternatives considered and rejected for this box

- **Indic Parler-TTS 0.9B**: full AdamW needs ~14.4 GB per replica before activations; no 16 GB recipe; LoRA PR closed. Not practical.
- **Orpheus 3B Hindi**: LoRA fits one 16 GB GPU via Unsloth (T4 notebook), but single-GPU only, autoregressive and slow on A16, no Hinglish eval. Keep as a possible second baseline.
- **Duration predictor** (EraX fork `--use_duration_predictor`): reported buggy (EraX #16); upstream has only a stub. Not for v1.

## 2.8 Environment

- Upstream F5-TTS: `torch>=2.0`, `accelerate>=0.33`, `bitsandbytes`, `ema_pytorch`, `x_transformers`, `vocos`, `torchdiffeq`, `torchcodec` (needs ffmpeg libs), `gradio`, `hydra-core`. README example: Python 3.11, `torch==2.8.0+cu128`. Driver on server is 580 (CUDA 13.0) → cu128 wheels fine.
- Use **upstream** F5-TTS for training with `--exp_name F5TTS_Base`; the IndicF5 fork is a pre-v1 snapshot with hardcoded paths and a commented-out checkpoint loader. Use its `model.py` only for inference-parity checks.
- IndicXlit (for later eval/transliteration) needs fairseq → Python ≤3.10 or `fairseq-fixed` on 3.11. Separate venv when needed.

## 2.9 Sources

F5-TTS files: `src/f5_tts/train/finetune_cli.py`, `train/README.md`, `train/datasets/prepare_csv_wavs.py`, `configs/F5TTS_Base.yaml`, `model/trainer.py`, `model/dataset.py`, `model/cfm.py`, `train/finetune_gradio.py`; issues #832, #790, #57, #769, #39, #993; instavar/f5-tts-lora-finetuning. IndicF5: HF card + API, GitHub fork, arXiv 2505.20693 §training. Fine-tunes: tryorato/orato-tts-hindi-v1, Saravananravi/indicf5-hinglish + saravananravi08/indicf5-finetune, ehzawad/indicf5-bangla-tts. A16: NVIDIA PB-10518-001_v02, Lenovo LP1815.
