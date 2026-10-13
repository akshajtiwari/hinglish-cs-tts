"""Shortest and longest audio file of the exam, overall and per dataset (read-only).

Only each file's header is read (soundfile.info), never the audio samples, so it is fast.
    ~/projects/baselines-venv/bin/python scripts/step2_baselines/audio_durations.py ~/projects/hinglish-cs-tts
Prints one line per dataset and saves analysis/step2/audio_durations.json.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd
import soundfile


def dataset_of(path):
    """Dataset name from the file path: the folder after _exam/audio/, or after datasets/ (BVCC, MANGO)."""
    parts = path.split("/datasets/")[1].split("/")
    if parts[0] == "_exam":
        return parts[2]
    return parts[0]


def summary(clips):
    """Count, shortest, longest, average, total hours, file sizes and sample rates of a list of clips."""
    shortest = clips[0]
    longest = clips[0]
    total_seconds = 0.0
    sizes = []
    rates = set()
    for clip in clips:
        if clip["seconds"] < shortest["seconds"]:
            shortest = clip
        if clip["seconds"] > longest["seconds"]:
            longest = clip
        total_seconds += clip["seconds"]
        sizes.append(clip["megabytes"])
        rates.add(clip["sample_rate"])
    return {
        "files": len(clips),
        "min_seconds": round(shortest["seconds"], 2),
        "min_file": shortest["path"],
        "max_seconds": round(longest["seconds"], 2),
        "max_file": longest["path"],
        "mean_seconds": round(total_seconds / len(clips), 2),
        "total_hours": round(total_seconds / 3600, 2),
        "min_megabytes": round(min(sizes), 3),
        "max_megabytes": round(max(sizes), 3),
        "sample_rates": sorted(rates),
    }


def main():
    base = Path(sys.argv[1]).expanduser()
    paths = pd.read_csv(base / "datasets" / "_exam" / "audio_list.csv")["path"]

    clips_by_dataset = {"ALL": []}
    for path in paths:
        info = soundfile.info(path)
        clip = {
            "path": path,
            "seconds": info.frames / info.samplerate,
            "sample_rate": info.samplerate,
            "megabytes": os.path.getsize(path) / 1e6,
        }
        dataset = dataset_of(path)
        if dataset not in clips_by_dataset:
            clips_by_dataset[dataset] = []
        clips_by_dataset[dataset].append(clip)
        clips_by_dataset["ALL"].append(clip)

    report = {}
    for dataset in clips_by_dataset:
        result = summary(clips_by_dataset[dataset])
        report[dataset] = result
        print(f"{dataset}: {result['files']} files, shortest {result['min_seconds']} s, "
              f"longest {result['max_seconds']} s, average {result['mean_seconds']} s, "
              f"total {result['total_hours']} h, sample rates {result['sample_rates']}")

    out = base / "analysis" / "step2" / "audio_durations.json"
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=2))
    tmp.replace(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
