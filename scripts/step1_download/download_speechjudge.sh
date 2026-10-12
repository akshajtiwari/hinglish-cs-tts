#!/usr/bin/env bash
# Download SpeechJudge-Data (211 GB, all splits) with hf download. Run on the server inside tmux.
# Resumable: run it again to continue. SOURCE/WHY and the result go to logs/dl_speechjudge.log.
# Later replaced by download_speechjudge_and_somos.py, which also verifies the files.
cd ~/projects/hinglish-cs-tts
source hinglishtts/bin/activate
LOG=logs/dl_speechjudge.log
echo "$(date -Is) SOURCE https://huggingface.co/datasets/RMSnow/SpeechJudge-Data | WHY SpeechJudge: 99K modern TTS preference pairs incl. zh-en code-switched slice = main modern training data and SpeechJudge-Eval test" | tee -a "$LOG"
echo "$(date -Is) START speechjudge" | tee -a "$LOG"
hf download RMSnow/SpeechJudge-Data --repo-type dataset --local-dir datasets/speechjudge >>"$LOG" 2>&1
rc=$?
echo "$(date -Is) END speechjudge rc=$rc" | tee -a "$LOG"
