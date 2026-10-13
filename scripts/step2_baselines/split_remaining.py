"""Split the files UTMOSv2 has not scored yet into N lists, one per GPU job.

    ~/projects/baselines-venv/bin/python scripts/step2_baselines/split_remaining.py ~/projects/hinglish-cs-tts 4

Writes analysis/step2/scores_parts/part<i>/list.csv. Round-robin split, so every part starts with
SpeechArenaBench, then SpeechJudge, then the rest (the same order as --first speecharena_votes,speechjudge).
Refuses to run if the part lists already exist (jobs may be using them).
"""
import sys
from pathlib import Path

import pandas as pd

base = Path(sys.argv[1]).expanduser()
n_parts = int(sys.argv[2])
out_root = base / "analysis" / "step2" / "scores_parts"
if out_root.exists():
    sys.exit(f"{out_root} already exists; merge and remove it first")

all_paths = pd.read_csv(base / "datasets" / "_exam" / "audio_list.csv")["path"].tolist()
done = set(pd.read_csv(base / "analysis" / "step2" / "scores" / "utmosv2.csv")["path"])
remaining = [path for path in all_paths if path not in done]


def priority(path):
    """0 for SpeechArenaBench, 1 for SpeechJudge, 2 for the rest."""
    if "speecharena_votes" in path:
        return 0
    if "speechjudge" in path:
        return 1
    return 2


remaining.sort(key=priority)   # sort is stable, so the list order is kept inside each group
total = 0
for i in range(n_parts):
    folder = out_root / f"part{i}"
    folder.mkdir(parents=True)
    mine = remaining[i::n_parts]
    pd.DataFrame({"path": mine}).to_csv(folder / "list.csv", index=False)
    total += len(mine)
    print(f"part{i}: {len(mine)} files")
assert total == len(remaining)
print(f"{len(done)} already scored, {len(remaining)} split into {n_parts} parts")
