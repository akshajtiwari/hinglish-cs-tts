"""Does clip length explain why the predictors prefer one system? (Paper A section 5; question raised 25 Nov 2026.)

The predictors pick the longer clip of a vote far more often than listeners do, and the system they all rank first
(GPT-4o-mini) also makes the longest clips. To separate length from system, this holds the system fixed:
  1. how often each predictor (and the listeners) picks the longer clip, over all decided votes;
  2. in each pairing, how often the pairing's first system (by name) is picked when its clip is the longer one and when
     it is the shorter one, with 95% Wilson intervals; the difference is the length effect with the system held fixed;
  3. that length effect averaged over the six pairings, with a sentence-cluster bootstrap interval (2,000 draws,
     seed 15, as in the paper), comparable between predictors and listeners;
  4. what the votes on which all four predictors are wrong (or all right) are made of: how many involve the system
     every predictor ranks first (--top-system), and in how many of those its clip is the longer one.
Equal scores or equal lengths are left out of the "picks the longer clip" counts (they are a handful of votes).

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python scripts/step2_baselines/length_control.py \\
      --votes docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/votes_speecharena.csv \\
      --scores docs/ledger/artifacts/paper_a_revision_20261123/utmosv2_10runs/scores_mean \\
      --features docs/ledger/artifacts/failure_analysis_20261015/evidence/audio_features.csv \\
      --out docs/ledger/artifacts/paper_a_revision_20261123/final/length_control.json
"""
import argparse
import math
from pathlib import Path

import numpy

from analyze_judge_failures import JUDGES, group_by, read_csv
from switchmos import files

RATERS = JUDGES + ["listeners"]
ROUNDS = 2000
SEED = 15


def wilson(k, n):
    """95% Wilson interval of k successes out of n, as shares."""
    if n == 0:
        return [None, None]
    p = k / n
    z = 1.96
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [centre - half, centre + half]


def picks(row, rater, side):
    """True when the rater prefers the clip on this side ("a" or "b") of the vote."""
    other = "b" if side == "a" else "a"
    if rater == "listeners":
        return row["label"] == side.upper()
    return row[rater + "_" + side] > row[rater + "_" + other]


def prepare(votes, scores, seconds):
    """Decided votes with audio, each with every rater's two scores, both lengths and its pairing."""
    rows = []
    for vote in votes:
        if vote["label"] not in ("A", "B") or vote["audio_status"] != "ok":
            continue
        row = dict(vote)
        for judge in JUDGES:
            row[judge + "_a"] = scores[judge][vote["path_a"]]
            row[judge + "_b"] = scores[judge][vote["path_b"]]
        row["seconds_a"] = seconds[vote["path_a"]]
        row["seconds_b"] = seconds[vote["path_b"]]
        row["pairing"] = " vs ".join(sorted([vote["system_a"], vote["system_b"]]))
        rows.append(row)
    return rows


def first_side(row):
    """The side ("a" or "b") of the pairing's first system by name."""
    return "a" if row["system_a"] == row["pairing"].split(" vs ")[0] else "b"


def length_effect(rows, rater, weights=None, sentence_index=None):
    """Mean over pairings of P(pick first system | its clip longer) - P(pick it | its clip shorter), or None."""
    effects = []
    for pairing, group in sorted(group_by(rows, "pairing").items()):
        counts = {True: [0.0, 0.0], False: [0.0, 0.0]}
        for row in group:
            w = 1.0 if weights is None else weights[sentence_index[row["sentence_id"]]]
            side = first_side(row)
            other = "b" if side == "a" else "a"
            longer = row["seconds_" + side] > row["seconds_" + other]
            counts[longer][0] += w * picks(row, rater, side)
            counts[longer][1] += w
        if counts[True][1] == 0 or counts[False][1] == 0:
            return None
        effects.append(counts[True][0] / counts[True][1] - counts[False][0] / counts[False][1])
    return float(numpy.mean(effects))


def main():
    parser = argparse.ArgumentParser(description="Clip length versus system identity in predictor choices.")
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top-system", default="GPT 4o Mini TTS")
    args = parser.parse_args()

    scores = {}
    for judge in JUDGES:
        scores[judge] = {row["path"]: float(row["score"]) for row in read_csv(args.scores / (judge + ".csv"))}
    seconds = {row["path"]: float(row["seconds"]) for row in read_csv(args.features)}
    rows = prepare(read_csv(args.votes), scores, seconds)
    report = {"votes": len(rows), "picks_longer": {}, "pairings": {}, "length_effect": {}}

    for rater in RATERS:
        hits = 0
        n = 0
        for row in rows:
            if row["seconds_a"] == row["seconds_b"]:
                continue
            if rater != "listeners" and row[rater + "_a"] == row[rater + "_b"]:
                continue
            longer = "a" if row["seconds_a"] > row["seconds_b"] else "b"
            hits += picks(row, rater, longer)
            n += 1
        report["picks_longer"][rater] = {"share": hits / n, "n": n}

    for pairing, group in sorted(group_by(rows, "pairing").items()):
        block = {"first_system": pairing.split(" vs ")[0]}
        for longer in [True, False]:
            subset = []
            for row in group:
                side = first_side(row)
                other = "b" if side == "a" else "a"
                if (row["seconds_" + side] > row["seconds_" + other]) == longer:
                    subset.append((row, side))
            part = {"n": len(subset)}
            for rater in RATERS:
                k = sum(picks(row, rater, side) for row, side in subset)
                part[rater] = {"share": k / len(subset) if subset else None, "ci95": wilson(k, len(subset))}
            block["first_longer" if longer else "first_shorter"] = part
        report["pairings"][pairing] = block

    for name, wanted in [("all_wrong", False), ("all_right", True)]:
        group = []
        for row in rows:
            right = []
            for judge in JUDGES:
                if row[judge + "_a"] == row[judge + "_b"]:
                    right.append(None)
                else:
                    right.append(picks(row, judge, row["label"].lower()))
            if all(r is wanted for r in right):
                group.append(row)
        top = [row for row in group if args.top_system in (row["system_a"], row["system_b"])]
        top_longer = 0
        for row in top:
            side = "a" if row["system_a"] == args.top_system else "b"
            other = "b" if side == "a" else "a"
            top_longer += row["seconds_" + side] > row["seconds_" + other]
        report[name] = {"votes": len(group), "with_top_system": len(top), "top_system_clip_longer": top_longer,
                        "top_system": args.top_system}

    sentences = sorted({row["sentence_id"] for row in rows})
    index = {sentence: i for i, sentence in enumerate(sentences)}
    rng = numpy.random.default_rng(SEED)
    draws = {rater: [] for rater in RATERS}
    kept = 0
    for _ in range(ROUNDS):
        weights = numpy.bincount(rng.integers(0, len(sentences), len(sentences)), minlength=len(sentences)).astype(float)
        values = {rater: length_effect(rows, rater, weights, index) for rater in RATERS}
        if None in values.values():
            continue
        kept += 1
        for rater in RATERS:
            draws[rater].append(values[rater])
    report["draws_kept"] = kept
    for rater in RATERS:
        low, high = numpy.quantile(draws[rater], [0.025, 0.975])
        report["length_effect"][rater] = {"mean_over_pairings": length_effect(rows, rater), "ci95": [float(low), float(high)]}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    files.save_json(args.out, report)
    for rater in RATERS:
        effect = report["length_effect"][rater]
        print(f"{rater:10s} picks longer {100 * report['picks_longer'][rater]['share']:.1f}%  length effect "
              f"{100 * effect['mean_over_pairings']:+.1f} [{100 * effect['ci95'][0]:+.1f}, {100 * effect['ci95'][1]:+.1f}]")
    print("draws kept", kept)
    for name in ["all_wrong", "all_right"]:
        block = report[name]
        print(f"{name}: {block['votes']} votes, {block['with_top_system']} with {args.top_system}, its clip longer in "
              f"{block['top_system_clip_longer']}")


if __name__ == "__main__":
    main()
