# model/ — IndicF5 toolkit

Scripts and configs for IndicF5 (AI4Bharat's F5-TTS model for Indian languages). In the SwitchMOS plan they serve two purposes:

1. **Minimal pairs:** regenerate only a switch region of a real Hinglish clip (F5 infilling) to build before/after training pairs for the local-event branch.
2. **Optional test voice:** fine-tune IndicF5 on HiACC FT speakers as a modern Hinglish system not present in any rating dataset.

Documentation: `../switchmos/15_infrastructure.md` (server, environment, recipe) and `../switchmos/03_datasets.md` §3.5 (HiACC facts and speaker split).

| Step | Script | Where | What |
|---|---|---|---|
| 0 | `scripts/00_inspect_hiacc.py` | anywhere | Corpus layout and stats (stdlib only) |
| 1 | `scripts/01_prepare_hiacc.py` | server | 16→24 kHz, filtering, `--split-file configs/hiacc_speaker_split.json`, optional clip merging, `audio_file\|text` CSVs |
| — | `scripts/server_setup.sh` | server | torch cu128 + pinned F5-TTS into the `hinglishtts` venv (done) |
| 2 | `scripts/02_convert_indicf5_ckpt.py` | server | IndicF5 `model.safetensors` → trainer-loadable checkpoint |
| 3 | `scripts/03_train.sh` | server, tmux | Fine-tune on 4×A16 (not run; owner reviews code first) |
| — | `scripts/10_count_speecharena_codemix.py` | anywhere | Count code-mixed pairs per SpeechArenaBench language (text columns only) |

Configs: `configs/hiacc_speaker_split.json` (speaker-disjoint FT/REF/TEST), `configs/accelerate_4xa16.yaml` (4-process DDP, fp16), `configs/indicf5_vocab.txt` (2545 lines).
