#!/usr/bin/env bash
# One-time environment setup on the GPU server. Run from ~/projects/hinglish-cs-tts.
# Assumes: pyenv Python 3.11 pinned via .python-version, venv ./hinglishtts exists, ffmpeg installed.
set -euo pipefail
ROOT="$HOME/projects/hinglish-cs-tts"
F5_COMMIT="283252563dbf91be625e0c27926acfaac449186c"   # SWivid/F5-TTS main, 2026-09-21, v1.1.22
cd "$ROOT"
source hinglishtts/bin/activate
python --version

# 1. PyTorch cu128 (driver 580 / CUDA 13.0 on the box; Ampere sm_86 is in the wheel)
pip install -q torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128

# 2. F5-TTS at a pinned commit, editable install
if [ ! -d F5-TTS ]; then
  git clone -q https://github.com/SWivid/F5-TTS.git
fi
cd F5-TTS
git fetch -q
git checkout -q "$F5_COMMIT"
cd ..
pip install -q -e ./F5-TTS
pip install -q tensorboard huggingface_hub safetensors

# 3. sanity check
python "$ROOT/model/scripts/check_torch_setup.py"
which f5-tts_finetune-cli accelerate
echo "setup done"
