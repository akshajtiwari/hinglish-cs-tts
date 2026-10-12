#!/usr/bin/env bash
# Write a sha256 for every MANGO file (except Hugging Face's .cache folder) to mango.sha256, then print one hash of that list.
# Run on the server from ~/projects/hinglish-cs-tts/datasets. Read-only on the dataset.
set -e
# -print0 / sort -z / xargs -0 keep file names with spaces intact; sorting makes the list the same on every run
find mango -type f -not -path "*/.cache/*" -print0 | sort -z | xargs -0 sha256sum > mango.sha256
wc -l mango.sha256
sha256sum mango.sha256 | cut -c1-64
