"""Intervention for Paper A §V: do the judges still prefer GPT-4o-mini when loudness and edge silence are equalised?

Writes changed copies of every SAB vote clip, at the clip's own sample rate, as 32-bit float WAV (so loud copies
are not clipped), in two conditions:
  rms       every clip scaled to RMS 0.05 (about -26 dBFS)
  rms_trim  the same, after cutting leading and trailing silence (frames 35 dB below the loudest 20 ms frame, the
            rule of collect_failure_evidence.measure, so the cut matches the saved leading/trailing silence)
For each condition it writes <out>/<condition>/audio/<file name>, an audio list for score_baselines.py and a copy of
the votes table that points at the changed files, so paper_a_extra_analyses.py runs on it unchanged.
Files already written are kept (resumable).

Run (server, tmux):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/normalise_audio.py \\
      --votes ~/projects/hinglish-cs-tts/datasets/_exam/votes_speecharena.csv \\
      --out ~/projects/hinglish-cs-tts/datasets/_exam/normalised
  then, per condition and judge (utmos, distillmos, scoreq):
  score_baselines.py --scorer <judge> --list <out>/<condition>/audio_list.csv --out <scores folder>/<condition>
"""
import argparse
import csv
from pathlib import Path

import numpy

from switchmos.audio import load_audio

TARGET_RMS = 0.05


def trim_edges(wav, sr):
    """Cut leading and trailing 20 ms frames that are 35 dB or more below the loudest frame."""
    size = max(1, round(sr * 0.020))
    energy = []
    for start in range(0, len(wav), size):
        piece = wav[start:start + size].astype("float64")
        energy.append(float(numpy.sqrt(numpy.mean(piece * piece))))
    energy = numpy.array(energy)
    voiced = numpy.flatnonzero(energy > energy.max() * 10 ** (-35 / 20))
    if len(voiced) == 0:
        return wav
    return wav[int(voiced[0]) * size:(int(voiced[-1]) + 1) * size]


def change(wav, sr, condition):
    if condition == "rms_trim":
        wav = trim_edges(wav, sr)
    rms = float(numpy.sqrt(numpy.mean(wav.astype("float64") ** 2)))
    return (wav * (TARGET_RMS / max(rms, 1e-9))).astype("float32")


def main():
    parser = argparse.ArgumentParser(description="Loudness-normalised (and edge-trimmed) copies of SAB vote clips.")
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    import soundfile
    with open(args.votes) as f:
        votes = list(csv.DictReader(f))
    paths = set()
    for row in votes:
        if row["audio_status"] == "ok":
            paths.add(row["path_a"])
            paths.add(row["path_b"])
    for condition in ["rms", "rms_trim"]:
        folder = args.out / condition / "audio"
        folder.mkdir(parents=True, exist_ok=True)
        new_path = {}
        for path in sorted(paths):
            target = folder / Path(path).name
            new_path[path] = str(target)
            if target.exists():
                continue
            wav, sr = load_audio(path)
            temporary = target.with_suffix(".tmp.wav")
            soundfile.write(temporary, change(wav, sr, condition), sr, subtype="FLOAT")
            temporary.replace(target)
        with open(args.out / condition / "audio_list.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["path"])
            for path in sorted(new_path.values()):
                writer.writerow([path])
        with open(args.out / condition / "votes_speecharena.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(votes[0]))
            writer.writeheader()
            for row in votes:
                row = dict(row)
                if row["audio_status"] == "ok":
                    row["path_a"] = new_path[row["path_a"]]
                    row["path_b"] = new_path[row["path_b"]]
                writer.writerow(row)
        print(f"{condition}: {len(new_path)} clips in {folder}", flush=True)


if __name__ == "__main__":
    main()
