#!/usr/bin/env bash
# Step 2: a separate pyenv venv for the baseline scorers (keeps the IndicF5 venv hinglishtts untouched).
# Each package group is installed on its own, so one failure does not stop the others.
# Everything is logged, and the final package list is saved with pip freeze.
set -eu
BASE="$HOME/projects/hinglish-cs-tts"
LOG="$BASE/logs/step2_env.log"
VENV="$HOME/projects/baselines-venv"

say() {
  echo "$(date -Is) $*" | tee -a "$LOG"
}

if [ ! -x "$VENV/bin/python" ]; then
  "$HOME/.pyenv/versions/3.11.16/bin/python" -m venv "$VENV"
  say "created venv $VENV (Python 3.11.16 from pyenv)"
fi
if ! "$VENV/bin/pip" install -q -U pip wheel >> "$LOG" 2>&1; then
  say "FAILED: pip upgrade"
fi

say "installing torch 2.8.0 + torchaudio (CUDA 12.8 wheels, same as the main venv)"
if ! "$VENV/bin/pip" install -q torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 >> "$LOG" 2>&1; then
  say "FAILED: torch"
fi

for GROUP in "soundfile librosa pandas pyarrow scipy tqdm" \
             "git+https://github.com/sarulab-speech/UTMOSv2.git" \
             "distillmos" \
             "scoreq"; do
  # $GROUP is not quoted on purpose: the first group splits into several package names
  if "$VENV/bin/pip" install -q $GROUP >> "$LOG" 2>&1; then
    say "installed: $GROUP"
  else
    say "FAILED to install: $GROUP (see log)"
  fi
done

"$VENV/bin/python" -c "import torch, torchaudio; print('torch', torch.__version__, '| torchaudio', torchaudio.__version__, '| cuda available', torch.cuda.is_available())" 2>&1 | tee -a "$LOG"
for MODULE in utmosv2 distillmos scoreq scipy soundfile; do
  "$VENV/bin/python" -c "import $MODULE; print('import ok: $MODULE', getattr($MODULE, '__version__', ''))" 2>&1 | tail -1 | tee -a "$LOG"
done

"$VENV/bin/pip" freeze > "$BASE/logs/step2_env_freeze.txt"
COUNT=$(wc -l < "$BASE/logs/step2_env_freeze.txt")
say "frozen package list: $BASE/logs/step2_env_freeze.txt ($COUNT packages)"
say "DONE"
