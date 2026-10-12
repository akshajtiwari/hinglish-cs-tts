#!/usr/bin/env bash
# Download batch 2: BVCC, MUCS Hindi-English (test + train) and SOMOS.
# Run on the server; it works in ~/projects/hinglish-cs-tts. Each dataset gets a SOURCE/WHY line in logs/dl_batch2.log.
# Zenodo files are checked against the md5 Zenodo publishes; OpenSLR publishes none.
# No "set -e": a failed download is logged and the script goes on with the next file (wget -c resumes on a re-run).
set -u
cd ~/projects/hinglish-cs-tts
mkdir -p datasets logs
LOG=logs/dl_batch2.log

say() {
  echo "$(date -Is) $*" | tee -a "$LOG"
}

# usage: fetch <dataset folder> <url> <file name> <md5, or - when none is published>
fetch() {
  name="$1"
  url="$2"
  file="$3"
  md5="$4"
  path="datasets/$name/$file"
  mkdir -p "datasets/$name"
  say "START $name $file"
  wget -c -q --show-progress --progress=dot:giga -O "$path" "$url" >>"$LOG" 2>&1
  rc=$?
  size=$(stat -c %s "$path" 2>/dev/null)
  if [ "$md5" = "-" ]; then
    say "END $name $file rc=$rc bytes=$size md5=n/a(sha256 recorded later)"
    return
  fi
  got=$(md5sum "$path" | cut -d' ' -f1)
  if [ "$got" = "$md5" ]; then
    say "END $name $file rc=$rc bytes=$size md5=OK"
  else
    say "END $name $file rc=$rc bytes=$size md5=MISMATCH got=$got want=$md5"
  fi
}

say "SOURCE https://zenodo.org/records/10691660 | WHY BVCC: classic MOS benchmark for training, no-harm test, and the UTMOS reproduction gate"
fetch bvcc https://zenodo.org/api/records/10691660/files/main.tar.gz/content main.tar.gz ba4b896801282ca0eae37b9fd81ed94c
fetch bvcc https://zenodo.org/api/records/10691660/files/ood.tar.gz/content ood.tar.gz 3f606518cd99138784380482d0c38e48
fetch bvcc https://zenodo.org/api/records/10691660/files/scoring_program_distribute.tar.gz/content scoring_program_distribute.tar.gz 11e21b41dd88f33b64c17481a9281722

say "SOURCE https://www.openslr.org/104/ | WHY MUCS Hindi-English: natural code-switched speech for the local switch branch (Hindi-English only per v1 scope)"
fetch mucs_hi_en https://openslr.trmal.net/resources/104/Hindi-English_test.tar.gz Hindi-English_test.tar.gz -
fetch mucs_hi_en https://openslr.trmal.net/resources/104/Hindi-English_train.tar.gz Hindi-English_train.tar.gz -

say "SOURCE https://zenodo.org/records/7378801 | WHY SOMOS: 375k absolute MOS ratings for scale and calibration, among the most useful sets in UTMOSv2"
fetch somos https://zenodo.org/api/records/7378801/files/somos.zip/content somos.zip bdfde4cae256549dfab05d713136e4af

say "BATCH2 DONE"
