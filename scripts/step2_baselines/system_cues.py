"""Per-system audio cues on SAB decided votes, and how each judge's score follows them inside a system (Paper A §V).

One row per clip heard in a decided vote with audio (as in Table II). Cues, from the saved audio_features.csv
(collect_failure_evidence.measure, 20 ms frames, quiet = 35 dB below the clip's loudest frame):
  seconds, sample_rate, rms_dbfs, peak_dbfs, clipped (share of samples at full scale), leading/trailing silence,
  longest pause, quiet share, letters per voiced second (letters of the sentence / non-quiet seconds), and
  bandwidth_hz (99% of spectral energy) when --bandwidth is given (audio_bandwidth.py, server).
Writes:
  <out>/clip_cues.csv     path + every cue, usable as --features for paper_a_extra_analyses.py (listener side:
                          "pick the clip with more of this cue" as a rule, winner-balanced)
  <out>/system_cues.json  per system: clips, sample rates, median and quartiles of each cue, mean judge scores, and
                          the within-system Spearman correlation of each judge's score with each cue (judge side)

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python scripts/step2_baselines/system_cues.py \\
      --votes docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/votes_speecharena.csv \\
      --features docs/ledger/artifacts/failure_analysis_20261015/evidence/audio_features.csv \\
      --pairs docs/ledger/artifacts/failure_analysis_20261015/inputs/speecharena_pairs.parquet \\
      --scores docs/ledger/artifacts/failure_analysis_20261015/inputs/scores --out <folder> [--bandwidth <csv>]
"""
import argparse
import math
from pathlib import Path

import numpy

from analyze_judge_failures import JUDGES, read_csv, save_rows
from switchmos import files
from switchmos.eval.metrics import pearson, rankdata

CUES = ["seconds", "rms_dbfs", "peak_dbfs", "clipped", "leading_silence", "trailing_silence", "longest_pause",
        "quiet_share", "letters_per_voiced_second"]


def letters(text):
    """Number of letters (Unicode category L*; Devanagari vowel signs are not counted)."""
    count = 0
    for ch in text:
        if ch.isalpha():
            count += 1
    return count


def clip_cues(feature, text):
    """The cue values of one clip from its audio_features.csv row and its sentence."""
    seconds = float(feature["seconds"])
    quiet_share = float(feature["quiet_relative_fraction"])
    voiced_seconds = seconds * (1 - quiet_share)
    return {
        "seconds": seconds,
        "sample_rate": int(feature["sample_rate"]),
        "rms_dbfs": 20 * math.log10(max(float(feature["rms"]), 1e-9)),
        "peak_dbfs": 20 * math.log10(max(float(feature["peak"]), 1e-9)),
        "clipped": float(feature["near_full_scale_fraction"]),
        "leading_silence": float(feature["leading_quiet_seconds"]),
        "trailing_silence": float(feature["trailing_quiet_seconds"]),
        "longest_pause": float(feature["longest_quiet_seconds"]),
        "quiet_share": quiet_share,
        "letters_per_voiced_second": letters(text) / voiced_seconds if voiced_seconds > 0 else 0.0,
    }


def spearman(x, y):
    """Spearman correlation, or None when either side is constant."""
    if len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return pearson(rankdata(x), rankdata(y))


def summarise(clips, cues, judges):
    """{system: summary} over clip rows that carry system, every cue and every judge's score."""
    by_system = {}
    for clip in clips:
        by_system.setdefault(clip["system"], []).append(clip)
    report = {}
    for system, rows in sorted(by_system.items()):
        rates = {}
        for row in rows:
            rates[str(row["sample_rate"])] = rates.get(str(row["sample_rate"]), 0) + 1
        block = {"clips": len(rows), "sample_rates": rates, "cues": {}, "judge_mean": {}, "within_system_spearman": {}}
        for cue in cues:
            values = numpy.array([row[cue] for row in rows])
            q25, median, q75 = numpy.quantile(values, [0.25, 0.5, 0.75])
            block["cues"][cue] = {"median": float(median), "q25": float(q25), "q75": float(q75)}
        for judge in judges:
            scores = [row[judge] for row in rows]
            block["judge_mean"][judge] = float(numpy.mean(scores))
            block["within_system_spearman"][judge] = {cue: spearman(scores, [row[cue] for row in rows]) for cue in cues}
        report[system] = block
    return report


def main():
    parser = argparse.ArgumentParser(description="Per-system audio cues and their link to judge scores.")
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, required=True, help="harmonized speecharena_pairs.parquet (transcripts)")
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--bandwidth", type=Path, default=None, help="csv with path,bandwidth_hz")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    import pyarrow.parquet
    transcripts = {}
    for row in pyarrow.parquet.read_table(args.pairs, columns=["sentence_id", "transcript"]).to_pylist():
        transcripts[row["sentence_id"]] = row["transcript"]
    features = {row["path"]: row for row in read_csv(args.features)}
    bandwidth = {}
    if args.bandwidth:
        bandwidth = {row["path"]: float(row["bandwidth_hz"]) for row in read_csv(args.bandwidth)}
    scores = {}
    for judge in JUDGES:
        scores[judge] = {row["path"]: float(row["score"]) for row in read_csv(args.scores / (judge + ".csv"))}

    clips = {}
    for vote in read_csv(args.votes):
        if vote["label"] not in ("A", "B") or vote["audio_status"] != "ok":
            continue
        for side in ["a", "b"]:
            path = vote["path_" + side]
            if path in clips:
                continue
            row = {"path": path, "system": vote["system_" + side]}
            row.update(clip_cues(features[path], transcripts[vote["sentence_id"]]))
            if bandwidth:
                row["bandwidth_hz"] = bandwidth[path]
            for judge in JUDGES:
                row[judge] = scores[judge][path]
            clips[path] = row
    cues = list(CUES)
    if bandwidth:
        cues.append("bandwidth_hz")

    args.out.mkdir(parents=True, exist_ok=True)
    save_rows(args.out / "clip_cues.csv", list(clips.values()))
    report = {"clips": len(clips), "cues": cues, "judges": JUDGES, "systems": summarise(list(clips.values()), cues, JUDGES)}
    files.save_json(args.out / "system_cues.json", report)

    print(f"{len(clips)} clips")
    print("system".ljust(20) + "".join(cue[:12].rjust(13) for cue in cues))
    for system, block in report["systems"].items():
        print(system[:19].ljust(20) + "".join(f"{block['cues'][cue]['median']:13.3f}" for cue in cues))
    for system, block in report["systems"].items():
        for judge in JUDGES:
            values = block["within_system_spearman"][judge]
            print(f"{system[:19]:20s}{judge:11s}" + " ".join(f"{cue[:8]}={values[cue]:+.2f}" for cue in cues
                                                             if values[cue] is not None))


if __name__ == "__main__":
    main()
