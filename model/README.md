# model/ — fine-tuning IndicF5 on HiACC

Self-contained. Clone the repo onto the GPU server and run the scripts in order. Research docs for this folder are in `model/docs/`.

| Step | Script | Where | What |
|---|---|---|---|
| 0 | `scripts/00_inspect_hiacc.py` | anywhere | Corpus layout and stats (stdlib only) |
| 1 | `scripts/01_prepare_hiacc.py` | server | 16→24 kHz, filter, optional merge of short consecutive clips, `audio_file\|text` CSVs + JSONL manifests |
| — | `scripts/server_setup.sh` | server | torch cu128 + pinned F5-TTS into the `hinglishtts` venv |
| 2 | `scripts/02_convert_indicf5_ckpt.py` | server | gated IndicF5 `model.safetensors` → Trainer-loadable `pretrained_indicf5_base.safetensors` |
| 3 | `scripts/03_train.sh` | server, in tmux | arrow dataset + `accelerate launch` fine-tune on 4×A16 |

Configs: `configs/accelerate_4xa16.yaml` (4-process DDP, fp16), `configs/indicf5_vocab.txt` (2545 lines, index 0 = space).

Env overrides for `03_train.sh`: `LR=1e-5 FRAMES=12800 EPOCHS=100 EXTRA="--bnb_optimizer"`.

Docs:
- `docs/01_hiacc_data_analysis.md` — what the corpus really contains (1.46 h mixed of 3.22 h adult).
- `docs/02_finetuning_recipe.md` — hardware facts, verified trainer behaviour, hyperparameters, ablations, sources.

Server layout (`~/projects/hinglish-cs-tts/`): `hinglishtts/` venv · `F5-TTS/` pinned clone · `data/` corpus + prepared · `checkpoints/` converted pretrain · `logs/` · `model/` this folder.
