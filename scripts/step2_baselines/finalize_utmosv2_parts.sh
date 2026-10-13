#!/usr/bin/env bash
# Wait for the 4 UTMOSv2 part jobs to end; if every part is complete, merge them into scores/utmosv2.csv
# and run the final evaluation into analysis/step2/final_20261013/. Run inside tmux -L switchmos:
#   tmux -L switchmos new-session -d -s finalize "bash scripts/step2_baselines/finalize_utmosv2_parts.sh > ~/projects/hinglish-cs-tts/logs/step2_finalize_utmosv2.out 2>&1"
set -u
B="$HOME/projects/hinglish-cs-tts"
P="$B/analysis/step2/scores_parts"
PY="$HOME/projects/baselines-venv/bin/python"
CODE="$HOME/projects/switchmos_code"
export PYTHONPATH="$CODE/src"

say() {
  echo "$(date -Is) $*"
}

for i in 0 1 2 3; do
  while tmux -L switchmos has-session -t "utmosv2_g$i" 2>/dev/null; do
    sleep 15
  done
done
say "all 4 part jobs ended"

for i in 0 1 2 3; do
  done_rows=$(($(wc -l < "$P/part$i/utmosv2.csv") - 1))
  list_rows=$(($(wc -l < "$P/part$i/list.csv") - 1))
  error_rows=$(($(wc -l < "$P/part$i/utmosv2_errors.csv") - 1))
  say "part$i: $done_rows scored + $error_rows errors of $list_rows"
  if [ $((done_rows + error_rows)) -lt "$list_rows" ]; then
    say "part$i is not complete: NOT merging (restart the part jobs first)"
    exit 1
  fi
done

say "merging"
"$PY" "$CODE/scripts/step2_baselines/merge_parts.py" "$B" || { say "merge FAILED"; exit 1; }
say "scores/utmosv2.csv now has $(($(wc -l < "$B/analysis/step2/scores/utmosv2.csv") - 1)) rows"

say "final evaluation"
cd "$CODE" || exit 1
"$PY" scripts/step2_baselines/evaluate_baselines.py --root "$B/datasets" --scores "$B/analysis/step2/scores" \
  --out "$B/analysis/step2/final_20261013" || { say "evaluation FAILED"; exit 1; }
say "DONE: $B/analysis/step2/final_20261013/results.md"
