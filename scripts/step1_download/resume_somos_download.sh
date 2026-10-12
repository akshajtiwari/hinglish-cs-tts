#!/usr/bin/env bash
# Resume the SOMOS download on a new connection (the first one was throttled to about 58 KB/s by Zenodo).
# Uses the public records URL instead of the API URL. wget -c continues from the bytes already on disk.
# Later replaced by download_speechjudge_and_somos.py.
cd ~/projects/hinglish-cs-tts
LOG=logs/dl_batch2.log
ZIP=datasets/somos/somos.zip
echo "$(date -Is) RESTART somos via zenodo records URL, resuming from $(stat -c %s "$ZIP") bytes" >> "$LOG"
wget -c -q --show-progress --progress=dot:mega -O "$ZIP" "https://zenodo.org/records/7378801/files/somos.zip?download=1" >> "$LOG" 2>&1
rc=$?
echo "$(date -Is) END somos rc=$rc bytes=$(stat -c %s "$ZIP") md5=$(md5sum "$ZIP" | cut -d' ' -f1) want=bdfde4cae256549dfab05d713136e4af" >> "$LOG"
