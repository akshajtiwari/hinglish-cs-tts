#!/usr/bin/env bash
# Build the F5-TTS dataset from the prepared CSV and launch fine-tuning on 4×A16.
# Run inside tmux on the server from ~/projects/hinglish-cs-tts:
#     bash model/scripts/03_train.sh [run_name]
set -euo pipefail
ROOT="$HOME/projects/hinglish-cs-tts"
RUN="${1:-hinglish_v1}"
CSV="$ROOT/data/hiacc24k/train.csv"                       # from 01_prepare_hiacc.py
VOCAB="$ROOT/model/configs/indicf5_vocab.txt"             # IndicF5 checkpoints/vocab.txt (2545 lines)
PRETRAIN="$ROOT/checkpoints/pretrained_indicf5_base.safetensors"   # from 02_convert_indicf5_ckpt.py
ACC="$ROOT/model/configs/accelerate_4xa16.yaml"
F5="$ROOT/F5-TTS"
cd "$ROOT"; source hinglishtts/bin/activate

[ -f "$CSV" ] || { echo "missing $CSV"; exit 1; }
[ -f "$PRETRAIN" ] || { echo "missing $PRETRAIN"; exit 1; }
[ "$(wc -l < "$VOCAB")" -eq 2545 ] || { echo "vocab must have 2545 lines"; exit 1; }

# 1. arrow dataset (F5 expects data/<name>_custom/ under the repo root); then replace the Emilia vocab it copies
DS="$F5/data/${RUN}_custom"
if [ ! -f "$DS/raw.arrow" ]; then
  python "$F5/src/f5_tts/train/datasets/prepare_csv_wavs.py" "$CSV" "$DS" --workers 8
fi
cp "$VOCAB" "$DS/vocab.txt"
python - "$DS" <<'PY'
import json, sys; d=json.load(open(sys.argv[1]+"/duration.json"))["duration"]
print(f"dataset: {len(d)} clips, {sum(d)/3600:.2f} h, min {min(d):.2f}s max {max(d):.2f}s")
PY

# 2. train
mkdir -p "$ROOT/logs"
LOG="$ROOT/logs/${RUN}_$(date +%Y%m%d_%H%M%S).log"
echo "logging to $LOG"
cd "$F5"
accelerate launch --config_file "$ACC" src/f5_tts/train/finetune_cli.py \
  --exp_name F5TTS_Base \
  --dataset_name "$RUN" \
  --tokenizer custom --tokenizer_path "$VOCAB" \
  --finetune --pretrain "$PRETRAIN" \
  --learning_rate "${LR:-2e-5}" \
  --batch_size_per_gpu "${FRAMES:-8192}" --batch_size_type frame --max_samples 32 \
  --grad_accumulation_steps 1 --max_grad_norm 1.0 \
  --epochs "${EPOCHS:-60}" --num_warmup_updates 100 \
  --save_per_updates 250 --last_per_updates 50 --keep_last_n_checkpoints 5 \
  --log_samples --logger tensorboard \
  ${EXTRA:-} 2>&1 | tee "$LOG"
