#!/usr/bin/env bash
# Download one file from a slow host (Zenodo) in N parallel HTTP range requests, then check its md5.
# Usage: download_in_parts.sh <url> <dest> <md5> [N, default 16]
# Resumable: an existing complete file with the right md5 is kept.
set -eu
URL="$1"
DEST="$2"
WANT="$3"
N=16
if [ $# -ge 4 ]; then
  N="$4"
fi
LOG="$HOME/projects/hinglish-cs-tts/logs/fetch_parallel.log"

say() {
  echo "$(date -Is) $*" | tee -a "$LOG"
}

mkdir -p "$(dirname "$DEST")"
if [ -f "$DEST" ]; then
  HAVE=$(md5sum "$DEST" | cut -d' ' -f1)
  if [ "$HAVE" = "$WANT" ]; then
    say "already complete: $DEST"
    exit 0
  fi
fi

# total size from the last Content-Length header (after redirects)
TOTAL=$(curl -sIL "$URL" | grep -i '^content-length:' | tail -1 | cut -d' ' -f2 | tr -d '\r')
if [ -z "$TOTAL" ]; then
  say "FAILED: no content-length for $URL"
  exit 1
fi
PARTS=$(mktemp -d "$(dirname "$DEST")/.parts.XXXXXX")
PART_SIZE=$(( (TOTAL + N - 1) / N ))
say "fetching $URL ($TOTAL bytes) in $N parts"

# start one curl per byte range in the background, then wait for all of them
for i in $(seq 0 $((N - 1))); do
  START=$((i * PART_SIZE))
  END=$((START + PART_SIZE - 1))
  if [ "$END" -ge "$TOTAL" ]; then
    END=$((TOTAL - 1))
  fi
  if [ "$START" -le "$END" ]; then
    echo "$i $START $END" >> "$PARTS/jobs"
    curl -sS --retry 5 --retry-delay 3 -r "$START-$END" "$URL" -o "$PARTS/part.$i" &
  fi
done
wait

while read -r i START END; do
  SIZE=0
  if [ -f "$PARTS/part.$i" ]; then
    SIZE=$(stat -c %s "$PARTS/part.$i")
  fi
  if [ "$SIZE" -ne $((END - START + 1)) ]; then
    say "FAILED: part $i incomplete"
    exit 1
  fi
done < "$PARTS/jobs"

TMP="$DEST.tmp"
rm -f "$TMP"
while read -r i START END; do
  cat "$PARTS/part.$i" >> "$TMP"
done < "$PARTS/jobs"
GOT=$(md5sum "$TMP" | cut -d' ' -f1)
if [ "$GOT" = "$WANT" ]; then
  mv "$TMP" "$DEST"
  rm -rf "$PARTS"
  say "OK md5 $GOT -> $DEST"
else
  say "FAILED md5 $GOT != $WANT"
  exit 1
fi
