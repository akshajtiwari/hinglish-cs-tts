#!/usr/bin/env bash
# After the 4 UTMOSv2 GPU jobs (utmosv2_g0 to utmosv2_g3): check that every part is complete,
# merge the parts into scores/utmosv2.csv, then run the final evaluation into analysis/step2/final_20261013/.
# Run inside tmux:
#   tmux -L switchmos new-session -d -s finalize "bash scripts/step2_baselines/finalize_utmosv2_parts.sh > ~/projects/hinglish-cs-tts/logs/step2_finalize_utmosv2.out 2>&1"
BASE="$HOME/projects/hinglish-cs-tts"
PARTS="$BASE/analysis/step2/scores_parts"
CODE="$HOME/projects/switchmos_code"
PY="$HOME/projects/baselines-venv/bin/python"
export PYTHONPATH="$CODE/src"

echo "$(date) waiting for the 4 GPU jobs to end"
for i in 0 1 2 3; do
  while tmux -L switchmos has-session -t "utmosv2_g$i" 2>/dev/null; do
    sleep 15
  done
done
echo "$(date) all 4 jobs ended"

# a part is complete when every file of its list was either scored or logged as an error
for i in 0 1 2 3; do
  scored=$(tail -n +2 "$PARTS/part$i/utmosv2.csv" | wc -l)
  failed=$(tail -n +2 "$PARTS/part$i/utmosv2_errors.csv" | wc -l)
  wanted=$(tail -n +2 "$PARTS/part$i/list.csv" | wc -l)
  echo "part$i: $scored scored, $failed failed, $wanted in the list"
  if [ $((scored + failed)) -lt "$wanted" ]; then
    echo "part$i is not finished: not merging. Restart the part jobs first."
    exit 1
  fi
done

echo "$(date) merging"
if ! "$PY" "$CODE/scripts/step2_baselines/merge_parts.py" "$BASE"; then
  echo "merge FAILED"
  exit 1
fi

echo "$(date) final evaluation"
cd "$CODE"
if ! "$PY" scripts/step2_baselines/evaluate_baselines.py --root "$BASE/datasets" \
    --scores "$BASE/analysis/step2/scores" --out "$BASE/analysis/step2/final_20261013"; then
  echo "evaluation FAILED"
  exit 1
fi
echo "$(date) DONE: $BASE/analysis/step2/final_20261013/results.md"
