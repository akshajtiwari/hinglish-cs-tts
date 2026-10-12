#!/usr/bin/env bash
# Finish the Blizzard 2016 archive when one connection is throttled (about 30 KB/s).
# Downloads the missing end of the file in 16 parallel HTTP range requests, appends the pieces in order
# to the partial file, then checks size and md5 (the md5 published in BVCC's 01_get.py).
# Safe to re-run: it recomputes what is missing. Logs to logs/bvcc_blizzard.log.
# Run on the server with nothing else writing to the archive (stop wget / 01_get.py first).
set -u
BASE=~/projects/hinglish-cs-tts
LOG="$BASE/logs/bvcc_blizzard.log"
F="$BASE/datasets/bvcc/main/blizzard/blizzard_wavs_and_scores_2016_release_version_1.tar.bz2"
URL=https://data.cstr.ed.ac.uk/blizzard/wavs_and_scores/blizzard_wavs_and_scores_2016_release_version_1.tar.bz2
WANT=fff9d42a97161835f2545e02e5392e06
N=16

say() {
  echo "$(date -Is) $*" | tee -a "$LOG"
}

# total size: the last Content-Length header (after redirects)
T=$(curl -sIL "$URL" | tr -d '\r' | grep -i '^content-length:' | tail -n 1 | cut -d' ' -f2)
if [ -z "$T" ]; then
  say "2016 parallel: FAILED, no content-length from the server"
  exit 1
fi
L=$(stat -c %s "$F")
say "2016 parallel: total $T bytes, local $L bytes, remaining $((T - L)) bytes, $N range requests"

if [ "$L" -lt "$T" ]; then
  D=$(mktemp -d "$(dirname "$F")/parts.XXXXXX")
  R=$((T - L))
  C=$(( (R + N - 1) / N ))    # piece size, rounded up so N pieces cover the rest
  for i in $(seq 0 $((N - 1))); do
    a=$((L + i * C))
    b=$((a + C - 1))
    if [ "$b" -ge "$T" ]; then
      b=$((T - 1))
    fi
    if [ "$a" -le "$b" ]; then
      echo "$i $a $b" >> "$D/jobs"
      curl -sS --retry 5 --retry-delay 3 -r "$a-$b" "$URL" -o "$D/part.$i" &
    fi
  done
  wait    # for all the curl downloads started above

  while read -r i a b; do
    got=$(stat -c %s "$D/part.$i" 2>/dev/null || echo 0)
    want=$((b - a + 1))
    if [ "$got" -ne "$want" ]; then
      say "2016 parallel: FAILED, part $i has $got bytes, expected $want; partial parts kept in $D"
      exit 1
    fi
  done < "$D/jobs"
  # the jobs file lists the parts in order of increasing offset
  while read -r i a b; do
    cat "$D/part.$i" >> "$F"
  done < "$D/jobs"
  rm -rf "$D"
fi

FINAL=$(stat -c %s "$F")
say "2016 parallel: size now $FINAL (expected $T), computing md5"
SUM=$(md5sum "$F" | cut -d' ' -f1)
if [ "$FINAL" -eq "$T" ] && [ "$SUM" = "$WANT" ]; then
  say "2016 parallel: md5 OK ($SUM)"
else
  say "2016 parallel: PROBLEM size $FINAL md5 $SUM (want $WANT)"
fi
