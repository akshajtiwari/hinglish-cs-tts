"""Split the files UTMOSv2 has not scored yet into N lists, one list per GPU job.

Run:
    ~/projects/baselines-venv/bin/python scripts/step2_baselines/split_remaining.py ~/projects/hinglish-cs-tts 4

Writes analysis/step2/scores_parts/part0/list.csv, part1/list.csv, and so on.
SpeechArenaBench files come first, then SpeechJudge, then the rest. The files are dealt out like playing cards
(first file to part 0, second file to part 1, ...), so every part starts with SpeechArenaBench.
It stops if the part folders already exist, because jobs may still be using them.
"""
import sys
from pathlib import Path

import pandas as pd


def priority(path):
    """0 for SpeechArenaBench, 1 for SpeechJudge, 2 for everything else."""
    if "speecharena_votes" in path:
        return 0
    if "speechjudge" in path:
        return 1
    return 2


def main():
    base = Path(sys.argv[1]).expanduser()
    n_parts = int(sys.argv[2])
    out_root = base / "analysis" / "step2" / "scores_parts"
    if out_root.exists():
        print(f"{out_root} already exists; merge and remove it first")
        sys.exit(1)

    all_paths = pd.read_csv(base / "datasets" / "_exam" / "audio_list.csv")["path"]
    done_paths = set(pd.read_csv(base / "analysis" / "step2" / "scores" / "utmosv2.csv")["path"])

    remaining = []
    for path in all_paths:
        if path not in done_paths:
            remaining.append(path)
    # sort keeps the original list order inside each group
    remaining.sort(key=priority)

    # deal the files out like cards
    parts = []
    for i in range(n_parts):
        parts.append([])
    for position in range(len(remaining)):
        parts[position % n_parts].append(remaining[position])

    for i in range(n_parts):
        folder = out_root / f"part{i}"
        folder.mkdir(parents=True)
        pd.DataFrame({"path": parts[i]}).to_csv(folder / "list.csv", index=False)
        print(f"part{i}: {len(parts[i])} files")
    print(f"{len(done_paths)} already scored, {len(remaining)} split into {n_parts} parts")


if __name__ == "__main__":
    main()
