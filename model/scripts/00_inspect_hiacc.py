#!/usr/bin/env python3
"""Inspect the HiACC corpus: folder layout, audio stats, transcripts and metadata files.

Standard library only, so it runs anywhere. Usage:
    python model/scripts/00_inspect_hiacc.py data/HiACC
"""
import json
import statistics
import sys
import wave
from pathlib import Path

if len(sys.argv) > 1:
    root = Path(sys.argv[1])
else:
    root = Path("data/HiACC")
if not root.exists():
    sys.exit(f"{root} not found")

print(f"== tree (depth 3) under {root}")
for path in sorted(root.rglob("*")):
    rel = path.relative_to(root)
    if len(rel.parts) > 3:
        continue
    if path.is_dir():
        print("  ", rel, "(dir)")
    elif rel.parts[-1].endswith((".csv", ".json", ".txt", ".md")):
        print("  ", rel, f"{path.stat().st_size} B")

print("\n== audio")
durations_by_folder = {}
sample_rates = {}
channels = {}
bit_depths = {}
for wav_path in root.rglob("*.wav"):
    try:
        with wave.open(str(wav_path)) as f:
            sr = f.getframerate()
            n_channels = f.getnchannels()
            bits = f.getsampwidth() * 8
            n_frames = f.getnframes()
    except Exception as error:  # any unreadable file is reported and skipped
        print("  unreadable:", wav_path, error)
        continue
    folder = "/".join(wav_path.relative_to(root).parts[:3])
    if folder not in durations_by_folder:
        durations_by_folder[folder] = []
    durations_by_folder[folder].append(n_frames / sr)
    sample_rates[sr] = sample_rates.get(sr, 0) + 1
    channels[n_channels] = channels.get(n_channels, 0) + 1
    bit_depths[bits] = bit_depths.get(bits, 0) + 1

total_seconds = 0.0
for folder, durations in sorted(durations_by_folder.items()):
    seconds = sum(durations)
    total_seconds += seconds
    print(f"  {folder:40s} n={len(durations):5d}  hours={seconds / 3600:6.2f}  mean={statistics.mean(durations):5.2f}s  "
          f"min={min(durations):5.2f}  max={max(durations):6.2f}  median={statistics.median(durations):5.2f}")
print(f"  TOTAL hours={total_seconds / 3600:.2f}   sample rates={sample_rates}  channels={channels}  bits={bit_depths}")

print("\n== transcripts (first 5 found)")
transcripts = sorted(root.rglob("*.txt"))
print("  count:", len(transcripts))
for path in transcripts[:5]:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    print("  ", path.relative_to(root), "->", text[:120])

print("\n== annotation / metadata files")
for path in sorted(root.rglob("*.json")) + sorted(root.rglob("*.csv")):
    print("  ", path.relative_to(root), path.stat().st_size, "B")
    try:
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                first_key = list(data.keys())[0]
                first_value = json.dumps(data[first_key], ensure_ascii=False)[:200]
                print("     keys:", len(data), "| first:", first_key, "->", first_value)
            elif isinstance(data, list):
                print("     items:", len(data), "| first:", json.dumps(data[0], ensure_ascii=False)[:200])
        else:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            print("     header:", lines[0][:160])
            if len(lines) > 1:
                print("     row1  :", lines[1][:160])
            else:
                print("     row1  :", "")
    except Exception as error:  # a file that does not parse is reported, not fatal
        print("     (could not parse)", error)
