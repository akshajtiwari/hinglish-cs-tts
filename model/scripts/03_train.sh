#!/usr/bin/env bash
# Build the F5-TTS dataset from the prepared CSV and start fine-tuning on 4 x A16.
# Run inside tmux on the server from ~/projects/hinglish-cs-tts:
#     bash model/scripts/03_train.sh [run_name]
set -euo pipefail
ROOT="$HOME/projects/hinglish-cs-tts"
RUN=hinglish_v1
if [ "$#" -ge 1 ] && [ -n "$1" ]; then
  RUN="$1"
fi
CSV="$ROOT/data/hiacc24k/FT.csv"                                   # from 01_prepare_hiacc.py --split-file model/configs/hiacc_speaker_split.json
VOCAB="$ROOT/model/configs/indicf5_vocab.txt"                      # IndicF5 checkpoints/vocab.txt (2545 lines)
PRETRAIN="$ROOT/checkpoints/pretrained_indicf5_base.safetensors"   # from 02_convert_indicf5_ckpt.py
ACC="$ROOT/model/configs/accelerate_4xa16.yaml"
F5="$ROOT/F5-TTS"

# settings that can be changed from outside, e.g.  LR=1e-5 EPOCHS=30 bash model/scripts/03_train.sh
LR="${LR:-2e-5}"
FRAMES="${FRAMES:-8192}"
EPOCHS="${EPOCHS:-60}"
EXTRA="${EXTRA:-}"    # extra finetune_cli.py flags

cd "$ROOT"
source hinglishtts/bin/activate

if [ ! -f "$CSV" ]; then
  echo "missing $CSV"
  exit 1
fi
if [ ! -f "$PRETRAIN" ]; then
  echo "missing $PRETRAIN"
  exit 1
fi
if [ "$(wc -l < "$VOCAB")" -ne 2545 ]; then
  echo "vocab must have 2545 lines"
  exit 1
fi

# 1. arrow dataset (F5 expects data/<name>_custom/ under its repo root); then replace the Emilia vocab it copies
DS="$F5/data/${RUN}_custom"
if [ ! -f "$DS/raw.arrow" ]; then
  python "$F5/src/f5_tts/train/datasets/prepare_csv_wavs.py" "$CSV" "$DS" --workers 8
fi
cp "$VOCAB" "$DS/vocab.txt"
python "$ROOT/model/scripts/print_dataset_stats.py" "$DS"

# 2. train
mkdir -p "$ROOT/logs"
LOG="$ROOT/logs/${RUN}_$(date +%Y%m%d_%H%M%S).log"
echo "logging to $LOG"
cd "$F5"
# $EXTRA is left unquoted on purpose so that several flags split into separate arguments
accelerate launch --config_file "$ACC" src/f5_tts/train/finetune_cli.py \
  --exp_name F5TTS_Base \
  --dataset_name "$RUN" \
  --tokenizer custom --tokenizer_path "$VOCAB" \
  --finetune --pretrain "$PRETRAIN" \
  --learning_rate "$LR" \
  --batch_size_per_gpu "$FRAMES" --batch_size_type frame --max_samples 32 \
  --grad_accumulation_steps 1 --max_grad_norm 1.0 \
  --epochs "$EPOCHS" --num_warmup_updates 100 \
  --save_per_updates 250 --last_per_updates 50 --keep_last_n_checkpoints 5 \
  --log_samples --logger tensorboard \
  $EXTRA 2>&1 | tee "$LOG"
