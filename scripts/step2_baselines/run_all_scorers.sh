#!/usr/bin/env bash
# Steps 2.3 + 2.4: run the four baseline scorers at the same time (one GPU each; SCOREQ's ONNX model runs on the CPU),
# wait for all of them, then evaluate. Resumable: a rerun skips files already scored.
# Each scorer logs to logs/step2_<scorer>.out.
set -eu
BASE="$HOME/projects/hinglish-cs-tts"
CODE="$HOME/projects/switchmos_code"
PY="$HOME/projects/baselines-venv/bin/python"
LIST="$BASE/datasets/_exam/audio_list.csv"
SCORES="$BASE/analysis/step2/scores"
LOG="$BASE/logs/step2_run_all.log"
export PYTHONPATH="$CODE/src"

say() {
  echo "$(date -Is) $*" | tee -a "$LOG"
}

if [ ! -f "$LIST" ]; then
  say "FAILED: $LIST missing (run prepare_exam_audio.py first)"
  exit 1
fi
LINES=$(wc -l < "$LIST")
say "starting 4 scorers in parallel on $((LINES - 1)) files"
cd "$CODE"

GPU=0
for SCORER in utmos utmosv2 distillmos scoreq; do
  CUDA_VISIBLE_DEVICES=$GPU "$PY" scripts/step2_baselines/score_baselines.py --scorer "$SCORER" \
    --list "$LIST" --out "$SCORES" > "$BASE/logs/step2_$SCORER.out" 2>&1 &
  GPU=$((GPU + 1))
done
wait

for SCORER in utmos utmosv2 distillmos scoreq; do
  say "$SCORER: $(tail -1 "$BASE/logs/step2_$SCORER.out")"
done

say "evaluating"
if "$PY" scripts/step2_baselines/evaluate_baselines.py --root "$BASE/datasets" --scores "$SCORES" \
    --out "$BASE/analysis/step2" > "$BASE/logs/step2_evaluate.out" 2>&1; then
  say "evaluation written: $BASE/analysis/step2/results.md"
else
  say "FAILED: evaluation (see logs/step2_evaluate.out)"
fi
say "DONE"
