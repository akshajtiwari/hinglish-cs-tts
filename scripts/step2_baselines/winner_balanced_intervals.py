"""95% intervals for winner-balanced accuracy on SpeechArenaBench, from the saved judge scores (no audio, no GPU).

Winner-balanced accuracy (15 Oct failure analysis): inside each system pairing, the judge's accuracy on the votes won
by one system and on the votes won by the other are averaged; then the pairings are averaged. Any rule that always
picks one system in a pairing gets exactly 50%. The 15 Oct run gave only point estimates; this adds intervals.

Intervals: the same paired sentence-cluster percentile bootstrap as analyze_judge_failures.py (2,000 draws, seed 15).
A draw is kept only if every pairing still has votes won by each of its two systems; the number kept is reported.
Exploratory: the test set was already inspected; intervals are descriptive, not corrected for multiple comparisons.

Subsets: all decided votes, Hinglish votes, and the three pairings without Indic F5 (the 26 Oct evaluation found that
recognising Indic F5 alone beats the baselines, L-0122).

Run from the project folder (laptop, pyenv Python with numpy):
  PYTHONPATH=src:scripts/step2_baselines ~/.pyenv/versions/3.12.0/bin/python \
      scripts/step2_baselines/winner_balanced_intervals.py \
      --inputs docs/ledger/artifacts/failure_analysis_20261015/inputs \
      --saved docs/ledger/artifacts/failure_analysis_20261015/results/analysis.json \
      --out docs/ledger/artifacts/winner_balanced_20261026
"""
import argparse
import math
from pathlib import Path

import numpy

from switchmos import files
from analyze_judge_failures import JUDGES, group_by, join_scores, read_csv, summary

ROUNDS = 2000
SEED = 15
INDIC = "Indic F5"


def load_votes(inputs):
    """Decided SAB votes with every judge's credit, exactly as in the 15 Oct analysis."""
    scores = {}
    for judge in JUDGES:
        lookup = {}
        for row in read_csv(inputs / "scores" / (judge + ".csv")):
            lookup[row["path"]] = float(row["score"])
            assert math.isfinite(lookup[row["path"]]), "Non-finite score"
        scores[judge] = lookup
    raw = read_csv(inputs / "exam" / "votes_speecharena.csv")
    assert len(raw) == 4444, "Expected 4,444 SAB vote rows"
    return join_scores(raw, scores, True)


def bootstrap_winner_balanced(rows):
    """Point estimate, 95% interval and kept draws of winner-balanced accuracy for every judge."""
    # like summary(): only pairings where each of the two systems wins at least one vote
    pairings = []
    for pairing, group in sorted(group_by(rows, "pairing").items()):
        if len(group_by(group, "winner")) == 2:
            pairings.append(pairing)
    kept_rows = []
    for row in rows:
        if row["pairing"] in pairings:
            kept_rows.append(row)
    rows = kept_rows
    sentences = sorted(group_by(rows, "sentence_id"))
    sentence_index = {}
    for i, sentence in enumerate(sentences):
        sentence_index[sentence] = i
    pairing_index = {}
    for i, pairing in enumerate(pairings):
        pairing_index[pairing] = i
    # counts[sentence, pairing, w] and credits[sentence, pairing, w, judge]; w = 0 if the first system (by name) won
    counts = numpy.zeros((len(sentences), len(pairings), 2))
    credits = numpy.zeros((len(sentences), len(pairings), 2, len(JUDGES)))
    for row in rows:
        s = sentence_index[row["sentence_id"]]
        p = pairing_index[row["pairing"]]
        first_system = row["pairing"].split(" vs ")[0]
        w = 0 if row["winner"] == first_system else 1
        counts[s, p, w] += 1
        for j, judge in enumerate(JUDGES):
            credits[s, p, w, j] += row[judge + "_credit"]
    assert numpy.all(counts.sum(axis=0) > 0), "A pairing has no votes won by one of its systems"
    rng = numpy.random.default_rng(SEED)
    kept = []
    for draw_number in range(ROUNDS):
        draw = rng.integers(0, len(sentences), size=len(sentences))
        n = counts[draw].sum(axis=0)
        if not numpy.all(n > 0):
            continue
        total = credits[draw].sum(axis=0)
        per_winner = total / n[:, :, None]
        kept.append(per_winner.mean(axis=1).mean(axis=0))
    kept = numpy.array(kept)
    point = summary(rows)
    result = {"votes": len(rows), "sentences": len(sentences), "pairings": pairings, "draws_kept": len(kept),
              "draws": ROUNDS}
    for j, judge in enumerate(JUDGES):
        low, high = numpy.quantile(kept[:, j], [0.025, 0.975])
        result[judge] = {"winner_balanced_macro": point[judge]["winner_balanced_macro"],
                         "ci95": [float(low), float(high)],
                         "share_of_draws_above_half": float(numpy.mean(kept[:, j] > 0.5)),
                         "micro_accuracy": point[judge]["micro"]}
    return result


def main():
    parser = argparse.ArgumentParser(description="Intervals for winner-balanced accuracy on SAB.")
    parser.add_argument("--inputs", type=Path, required=True, help="failure-analysis inputs folder")
    parser.add_argument("--saved", type=Path, required=True, help="15 Oct analysis.json, to check the point estimates")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    votes = load_votes(args.inputs)
    subsets = {"sab_all": votes, "sab_mixed": [], "sab_without_indic": []}
    for row in votes:
        if row["mixed"]:
            subsets["sab_mixed"].append(row)
        if INDIC not in row["pairing"]:
            subsets["sab_without_indic"].append(row)

    saved = files.load_json(args.saved)
    report = {"exploratory": True, "method": "paired sentence-cluster percentile bootstrap, 2,000 draws, seed 15; "
              "draws where a pairing loses one of its two winners are dropped", "subsets": {}}
    for name, rows in subsets.items():
        print("subset", name, len(rows), "votes", flush=True)
        result = bootstrap_winner_balanced(rows)
        if name in saved["subsets"]:
            for judge in JUDGES:
                expected = saved["subsets"][name]["summary"][judge]["winner_balanced_macro"]
                assert abs(result[judge]["winner_balanced_macro"] - expected) < 1e-9, f"{name} {judge} differs from 15 Oct"
        report["subsets"][name] = result
    args.out.mkdir(parents=True, exist_ok=True)
    files.save_json(args.out / "winner_balanced_intervals.json", report)
    for name, result in report["subsets"].items():
        cells = []
        for judge in JUDGES:
            value = result[judge]
            cells.append(f"{judge} {100 * value['winner_balanced_macro']:.1f} "
                         f"[{100 * value['ci95'][0]:.1f}, {100 * value['ci95'][1]:.1f}]")
        print(f"{name} (n {result['votes']}, draws kept {result['draws_kept']}): " + "; ".join(cells))
    print("DONE: point estimates match the 15 Oct analysis for sab_all and sab_mixed")


if __name__ == "__main__":
    main()
