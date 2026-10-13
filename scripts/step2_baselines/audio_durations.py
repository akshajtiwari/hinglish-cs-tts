"""Shortest and longest audio file in the 15,445-file exam, overall and per dataset (read-only).

Reads only each file's header (soundfile.info), never the audio samples, so it is fast.
    ~/projects/baselines-venv/bin/python scripts/step2_baselines/audio_durations.py ~/projects/hinglish-cs-tts
Prints a table and saves analysis/step2/audio_durations.json.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd
import soundfile

base = Path(sys.argv[1]).expanduser()
paths = pd.read_csv(base / "datasets" / "_exam" / "audio_list.csv")["path"]

rows = []
for path in paths:
    # dataset name: the folder after _exam/audio/ (SOMOS, SpeechJudge, SAB) or after datasets/ (BVCC, MANGO)
    parts = path.split("/datasets/")[1].split("/")
    if parts[0] == "_exam":
        dataset = parts[2]
    else:
        dataset = parts[0]
    info = soundfile.info(path)
    rows.append({
        "dataset": dataset,
        "path": path,
        "seconds": info.frames / info.samplerate,
        "sample_rate": info.samplerate,
        "megabytes": os.path.getsize(path) / 1e6,
    })
table = pd.DataFrame(rows)

report = {}
groups = [("ALL", table)]
for dataset in sorted(table["dataset"].unique()):
    groups.append((dataset, table[table["dataset"] == dataset]))
for name, part in groups:
    shortest = part.loc[part["seconds"].idxmin()]
    longest = part.loc[part["seconds"].idxmax()]
    report[name] = {
        "files": len(part),
        "min_seconds": round(float(shortest["seconds"]), 2),
        "min_file": shortest["path"],
        "max_seconds": round(float(longest["seconds"]), 2),
        "max_file": longest["path"],
        "mean_seconds": round(float(part["seconds"].mean()), 2),
        "total_hours": round(float(part["seconds"].sum()) / 3600, 2),
        "min_megabytes": round(float(part["megabytes"].min()), 3),
        "max_megabytes": round(float(part["megabytes"].max()), 3),
        "sample_rates": sorted(int(rate) for rate in part["sample_rate"].unique()),
    }
    r = report[name]
    print(f"{name:18} {r['files']:6} files  min {r['min_seconds']:6.2f} s  max {r['max_seconds']:6.2f} s  "
          f"mean {r['mean_seconds']:5.2f} s  total {r['total_hours']:5.2f} h  sizes {r['min_megabytes']}-{r['max_megabytes']} MB  "
          f"rates {r['sample_rates']}")

out = base / "analysis" / "step2" / "audio_durations.json"
tmp = out.with_name(out.name + ".tmp")
tmp.write_text(json.dumps(report, indent=2))
tmp.replace(out)
print(f"saved {out}")
