# model/: IndicF5 toolkit

Scripts and configs for IndicF5 (AI4Bharat's F5-TTS model for Indian languages). They are used for:

1. **Minimal pairs:** regenerate only the switch region of a real Hinglish clip (F5 infilling) to make before/after pairs.
2. **Optional test voice:** fine-tune IndicF5 on the HiACC FT speakers, giving a modern Hinglish system that is not in any rating dataset.

| Step | Script | Where | What |
|---|---|---|---|
| 0 | `scripts/00_inspect_hiacc.py` | anywhere | Corpus layout and stats (standard library only) |
| 1 | `scripts/01_prepare_hiacc.py` | server | 16 → 24 kHz, filtering, `--split-file configs/hiacc_speaker_split.json`, optional clip merging, `audio_file\|text` CSVs |
| — | `scripts/server_setup.sh` | server | torch cu128 + pinned F5-TTS into the `hinglishtts` venv; checks the install with `scripts/check_torch_setup.py` |
| 2 | `scripts/02_convert_indicf5_ckpt.py` | server | IndicF5 `model.safetensors` → checkpoint the F5-TTS trainer can load |
| 3 | `scripts/03_train.sh` | server, tmux | Fine-tune on 4 × A16; prints dataset stats with `scripts/print_dataset_stats.py` |
| — | `scripts/count_speecharena_codemix.py` | anywhere | Count code-mixed pairs per SpeechArenaBench language (text columns only) |

Configs:
- `configs/hiacc_speaker_split.json`: speaker-disjoint FT / REF / TEST lists. HiACC's own splits share speakers.
- `configs/accelerate_4xa16.yaml`: 4-process DDP, fp16.
- `configs/indicf5_vocab.txt`: IndicF5 vocabulary (2545 lines).
