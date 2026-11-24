"""UTMOSv2 over several runs (Paper A, prereg doc 21 section 7): how much do its scores and accuracies move?

Inputs: run 1 (the old unseeded run, <scores>/utmosv2.csv) and the seeded runs (<runs>/seed<k>/utmosv2.csv). Only clips
scored in every run are used, and the script stops if a pair-set clip is missing from any run.
For every run, and for the mean score over all runs:
  SAB decided votes: plain accuracy, winner-balanced accuracy and within-pairing AUC (point estimates, as in
  paper_a_extra_analyses.py); SpeechJudge test: accuracy. Equal scores count half.
Then mean ± SD of each measure over the runs, and the per-clip SD of the score (median, 95th percentile, max).
Writes <out>/utmosv2_runs.json and a scores folder <out>/scores_mean/ in which utmosv2.csv is the per-clip mean over
the runs for clips scored in every run, and run 1 for the rest (the rating corpora, scored once), while the other
judges' files are copied unchanged; so every analysis, including evaluate_baselines.py, can be rerun with --scores.

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python scripts/step2_baselines/utmosv2_runs_summary.py \\
      --scores docs/ledger/artifacts/failure_analysis_20261015/inputs/scores --runs <folder with seed2..seed10> \\
      --votes docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/votes_speecharena.csv \\
      --speechjudge docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/pairs_speechjudge.csv --out <folder>
"""
import argparse
import shutil
from pathlib import Path

import numpy

import paper_a_extra_analyses as extra
from analyze_judge_failures import JUDGES, credit, join_scores, read_csv
from switchmos import files


def read_scores(path):
    return {row["path"]: float(row["score"]) for row in read_csv(path)}


def sab_measures(votes, scores):
    """(plain accuracy, winner-balanced accuracy, AUC) of one UTMOSv2 score set on SAB decided votes."""
    rows = join_scores(votes, {"utmosv2": scores}, True, ["utmosv2"])
    sentences = sorted({row["sentence_id"] for row in rows})
    index = {sentence: i for i, sentence in enumerate(sentences)}
    ones = numpy.ones(len(sentences))
    pairings = extra.build_pairings(rows, index, ["utmosv2"])
    balanced, auc = extra.subset_measures(pairings, ones, ["utmosv2"])["utmosv2"]
    plain = float(numpy.mean([row["utmosv2_credit"] for row in rows]))
    return plain, balanced, auc


def speechjudge_accuracy(pairs, scores):
    return float(numpy.mean([credit(scores[p["path_a"]], scores[p["path_b"]], p["label"]) for p in pairs]))


def main():
    parser = argparse.ArgumentParser(description="UTMOSv2 run-to-run variation.")
    parser.add_argument("--scores", type=Path, required=True, help="folder with the four judges' saved scores (run 1)")
    parser.add_argument("--runs", type=Path, required=True, help="folder with seed<k>/utmosv2.csv")
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--speechjudge", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    runs = {"run1": read_scores(args.scores / "utmosv2.csv")}
    for folder in sorted(args.runs.glob("seed*"), key=lambda p: int(p.name[4:])):
        runs[folder.name] = read_scores(folder / "utmosv2.csv")
    votes = read_csv(args.votes)
    pairs = read_csv(args.speechjudge)
    needed = set()
    for row in votes:
        if row["audio_status"] == "ok":
            needed.update([row["path_a"], row["path_b"]])
    for pair in pairs:
        needed.update([pair["path_a"], pair["path_b"]])
    for name, scores in runs.items():
        missing = needed - set(scores)
        assert not missing, f"{name} lacks {len(missing)} pair-set clips, e.g. {sorted(missing)[0]}"

    common = set(runs["run1"])
    for scores in runs.values():
        common &= set(scores)
    matrix = numpy.array([[runs[name][path] for path in sorted(common)] for name in runs])
    # rounded as in the saved file, so equal means (scores sit on a 1/512 grid) tie here too and count half
    mean_scores = {path: round(float(value), 6) for path, value in zip(sorted(common), matrix.mean(axis=0))}
    clip_sd = matrix.std(axis=0, ddof=1)

    report = {"runs": list(runs), "clips_in_every_run": len(common), "per_run": {}, "over_runs": {}, "mean_score": {},
              "clip_sd": {"median": float(numpy.median(clip_sd)), "p95": float(numpy.quantile(clip_sd, 0.95)),
                          "max": float(clip_sd.max())}}
    for name, scores in runs.items():
        plain, balanced, auc = sab_measures(votes, scores)
        report["per_run"][name] = {"sab_accuracy": plain, "sab_winner_balanced": balanced, "sab_auc": auc,
                                   "speechjudge_accuracy": speechjudge_accuracy(pairs, scores)}
    for measure in ["sab_accuracy", "sab_winner_balanced", "sab_auc", "speechjudge_accuracy"]:
        values = [report["per_run"][name][measure] for name in runs]
        report["over_runs"][measure] = {"mean": float(numpy.mean(values)), "sd": float(numpy.std(values, ddof=1)),
                                        "min": float(min(values)), "max": float(max(values))}
    plain, balanced, auc = sab_measures(votes, mean_scores)
    report["mean_score"] = {"sab_accuracy": plain, "sab_winner_balanced": balanced, "sab_auc": auc,
                            "speechjudge_accuracy": speechjudge_accuracy(pairs, mean_scores)}

    folder = args.out / "scores_mean"
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["path,score"]
    for path in sorted(runs["run1"]):
        lines.append(f"{path},{mean_scores.get(path, runs['run1'][path]):.6f}")
    report["scores_mean_file"] = {"mean_of_runs": len(mean_scores), "run1_only": len(runs["run1"]) - len(mean_scores)}
    files.save_text(folder / "utmosv2.csv", "\n".join(lines) + "\n")
    for judge in JUDGES:
        if judge != "utmosv2":
            shutil.copyfile(args.scores / (judge + ".csv"), folder / (judge + ".csv"))
    files.save_json(args.out / "utmosv2_runs.json", report)

    print(f"{len(runs)} runs, {len(common)} clips in every run; per-clip SD median {report['clip_sd']['median']:.3f}, "
          f"95th pct {report['clip_sd']['p95']:.3f}, max {report['clip_sd']['max']:.3f}")
    for measure, block in report["over_runs"].items():
        print(f"{measure:22s} mean {block['mean']:.4f} sd {block['sd']:.4f} range [{block['min']:.4f}, {block['max']:.4f}]"
              f"  mean-score run {report['mean_score'][measure]:.4f}")


if __name__ == "__main__":
    main()
