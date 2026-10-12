#!/usr/bin/env bash
# Complete BVCC: extract main.tar.gz, build sv56, download the Blizzard audio and preprocess it.
# Steps from the BVCC README: 01_get.py (downloads 6 Blizzard archives, md5 checked) -> 02_gather.py
# -> 03_preprocess.py (sox to 16 kHz, sv56 loudness normalisation, sanity check).
# Run on the server inside tmux. Logs to logs/bvcc_blizzard.log and stops at the first failure.
# The user agreed to the Blizzard Challenge terms of use on 2026-10-05, so the y/n prompt of 01_get.py is answered 'y'.
# Terms: research/non-commercial use only; no redistribution; cite and acknowledge the organisers.
set -u
BASE=~/projects/hinglish-cs-tts
LOG="$BASE/logs/bvcc_blizzard.log"
PY="$BASE/hinglishtts/bin/python"

say() {
  echo "$(date -Is) $*" | tee -a "$LOG"
}

fail() {
  say "FAILED: $*"
  exit 1
}

cd "$BASE/datasets/bvcc" || fail "no datasets/bvcc"
if [ ! -d main ]; then
  say "extracting main.tar.gz (skipping macOS ._ metadata files)"
  tar -xzf main.tar.gz --exclude='._*' --exclude='*/._*' --warning=no-unknown-keyword 2>>"$LOG" || fail "extract"
fi
cd main || fail "no main/ directory"
say "extracted: $(find . -type f | wc -l) files; wavs in DATA/wav: $(ls DATA/wav 2>/dev/null | wc -l)"

say "building sv56 (ITU-T STL v2009, needs wget, tar, make, gcc)"
bash install_sv56.sh >>"$LOG" 2>&1 || fail "install_sv56.sh"
source ./env.sh
command -v sv56demo >/dev/null || fail "sv56demo not on PATH after build"
command -v sox >/dev/null || fail "sox missing"
say "sv56demo: $(command -v sv56demo) | sox: $(command -v sox) | gawk: $(command -v gawk)"

YEARS="2008 2009 2010 2011 2013 2016"

# A year whose extraction was cut off (server shutdown) would be skipped by 01_get.py because its folder exists.
# So every year folder without an ".extracted_<year>" marker is removed and extracted again; markers are written after success.
for y in $YEARS; do
  v=1
  if [ "$y" = 2013 ]; then
    v=2    # 2013 is release version 2, the other years version 1
  fi
  d="blizzard/blizzard_wavs_and_scores_${y}_release_version_${v}"
  if [ -d "$d" ] && [ ! -f "blizzard/.extracted_${y}" ]; then
    say "removing possibly incomplete extraction $d (no marker)"
    chmod -R u+rwX "$d" 2>/dev/null
    rm -rf "$d" || fail "could not remove $d"
  fi
done

ALL_MARKED=1
for y in $YEARS; do
  if [ ! -f "blizzard/.extracted_${y}" ]; then
    ALL_MARKED=0
  fi
done

if [ "$ALL_MARKED" = 1 ]; then
  # 01_get.py deletes the archives after extracting ("rm blizzard/*.tar.bz2"), so running it again would download 46 GB again.
  say "all six Blizzard years extracted and marked: skipping 01_get.py"
else
  START=$(wc -l < "$LOG")    # only warnings written in THIS run count (old runs left an "UH OH" line)
  say "01_get.py: downloading Blizzard 2008, 2009, 2010, 2011, 2013 (v2), 2016 (md5 checked by the script); answering y to the terms prompt for the user"
  echo y | "$PY" 01_get.py >>"$LOG" 2>&1
  rc=$?
  say "01_get.py exit code $rc"
  if tail -n +$((START + 1)) "$LOG" | grep -q "UH OH"; then
    fail "01_get.py reported a corrupted download in this run (see log)"
  fi
  if [ "$rc" -ne 0 ]; then
    fail "01_get.py"
  fi
  # all six years are now extracted completely
  for y in $YEARS; do
    touch "blizzard/.extracted_${y}"
  done
fi
say "Blizzard folders: $(ls -d blizzard/blizzard_wavs_and_scores_* 2>/dev/null | wc -l) of 6; size $(du -sh blizzard | cut -f1)"

say "02_gather.py"
"$PY" 02_gather.py >>"$LOG" 2>&1 || fail "02_gather.py"
say "gathered files: $(ls gathered 2>/dev/null | wc -l)"

say "03_preprocess.py (this takes a while)"
"$PY" 03_preprocess.py >>"$LOG" 2>&1 || fail "03_preprocess.py"

n=$(ls DATA/wav | wc -l)
say "final DATA/wav files: $n (expected 7106 listed utterances)"
for s in train val test; do
  say "$s list: $(wc -l < "DATA/sets/${s}_mos_list.txt") utterances"
done
if grep -q "all good" "$LOG"; then
  say "sanity check: all good"
else
  say "sanity check: 'all good' NOT found in log, inspect it"
fi
say "DONE"
