#!/usr/bin/env python3
"""Print the clip count, hours and shortest/longest clip of an F5-TTS dataset folder.

Usage (called by 03_train.sh):
    python model/scripts/print_dataset_stats.py <dataset folder with duration.json>
"""
import json
import sys

with open(sys.argv[1] + "/duration.json") as f:
    durations = json.load(f)["duration"]
print(f"dataset: {len(durations)} clips, {sum(durations) / 3600:.2f} h, min {min(durations):.2f}s max {max(durations):.2f}s")
