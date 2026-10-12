"""Step 2.4: evaluate the baseline scores on every exam.

Rating exams (correlation with the human mean scores, per clip; per system where there are enough systems):
  bvcc and somos test; mango by language, split and variant. MANGO is MUSHRA 0-100, so only SRCC/LCC (no MSE).
Pair exams (pairwise accuracy: did the higher score go to the clip people preferred):
  speechjudge test: all pairs, the sentence-disjoint pairs, the mixed (zh-en) pairs; always-pick-B baseline next to each.
  speecharena test: the exam unit is the VOTE (each vote heard its own fresh synthesis): decided votes overall, mixed,
  per system pairing, and the average over the six pairings (the main number, since system identity alone predicts a lot).
  Baselines: always-first and the stronger-system oracle. The rater agreement is agreement across different syntheses,
  not a human ceiling. Tie votes get a separate check: are the two scores close?
Clips whose audio is missing in the source (audio_status != ok) are left out and counted next to every result.
Writes <out>/results.json and <out>/results.md atomically.

Run (server):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/evaluate_baselines.py \
      --root ~/projects/hinglish-cs-tts/datasets --scores ~/projects/hinglish-cs-tts/analysis/step2/scores \
      --out ~/projects/hinglish-cs-tts/analysis/step2
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from switchmos import files
from switchmos.eval import metrics

SCORERS = ["utmos", "utmosv2", "distillmos", "scoreq"]
# raters heard different syntheses of the same item, so this is NOT a human ceiling
AGREEMENT_ACROSS_SYNTHESES = 0.714


def load_scores(scores_dir):
    """Read <scorer>.csv for every scorer that has one: {scorer: {path: score}}."""
    scores = {}
    for scorer in SCORERS:
        path = Path(scores_dir) / f"{scorer}.csv"
        if path.exists():
            df = pd.read_csv(path)
            scores[scorer] = dict(zip(df["path"], df["score"]))
    return scores


def rating_block(clips, scores, with_system=True):
    """Correlation of each scorer with the human mean scores on one rating exam."""
    results = {}
    n_audio_missing = int((clips["audio_status"] != "ok").sum())
    clips = clips[clips["audio_status"] == "ok"]
    for scorer, scores_of_path in scores.items():
        d = clips.copy()
        d["pred"] = d["path"].map(scores_of_path)
        d = d.dropna(subset=["pred"])
        if len(d) < 3:
            continue
        systems = None
        if with_system:
            systems = list(d["system"])
        report = metrics.regression_report(list(d["pred"]), list(d["mos"]), systems)
        report["n_audio_missing"] = n_audio_missing
        report["n_score_failed"] = int(len(clips) - len(d))
        rounded = {}
        for key, value in report.items():
            if isinstance(value, float):
                value = round(value, 4)
            rounded[key] = value
        results[scorer] = rounded
    return results


def accuracies(d, scores):
    """Pairwise accuracy per scorer on the rows that scorer has scored, plus that count,
    so a partial run can never look complete."""
    results = {}
    for scorer in scores:
        x = d.dropna(subset=[f"{scorer}_a", f"{scorer}_b"])
        accuracy = metrics.pairwise_accuracy(list(x[f"{scorer}_a"]), list(x[f"{scorer}_b"]), list(x["label"]))
        results[scorer] = round(accuracy, 4)
        results[f"n_{scorer}"] = len(x)
    return results


def table_cell(result, scorer, n):
    """Accuracy for the markdown table, with (n=...) when the scorer covered fewer than the n items of the exam."""
    text = f"{result.get(scorer, float('nan')):.3f}"
    n_scored = result.get(f"n_{scorer}")
    if n_scored is not None and n_scored < n:
        text += f" (n={n_scored})"
    return text


def stronger_system_oracle(d):
    """Accuracy of always picking, in each pairing of two systems, the system that wins more votes there."""
    if len(d) == 0:
        return float("nan")
    wins = {}
    for system_a, system_b, label in zip(d["system_a"], d["system_b"], d["label"]):
        pairing = "|".join(sorted([system_a, system_b]))
        if label == "A":
            winner = system_a
        else:
            winner = system_b
        if pairing not in wins:
            wins[pairing] = {}
        wins[pairing][winner] = wins[pairing].get(winner, 0) + 1
    total = 0
    for counts in wins.values():
        total += max(counts.values())
    return float(total / len(d))


def mean_abs_gap(d, scorer):
    """Mean absolute difference between the two scores of each pair."""
    gap = (d[f"{scorer}_a"] - d[f"{scorer}_b"]).abs().mean()
    return round(float(gap), 4)


def add_score_columns(df, scores):
    """Add <scorer>_a and <scorer>_b columns with the score of each clip."""
    for scorer, scores_of_path in scores.items():
        df[f"{scorer}_a"] = df["path_a"].map(scores_of_path)
        df[f"{scorer}_b"] = df["path_b"].map(scores_of_path)


def evaluate(exam, scores):
    """Compute every result and return them as one dict."""
    results = {"scorers": sorted(scores), "rating_exams": {}, "speechjudge": {}, "speecharena": {}}

    for name in ["bvcc", "somos"]:
        clips = pd.read_csv(exam / f"clips_{name}.csv")
        results["rating_exams"][name] = rating_block(clips[clips["split"] == "test"], scores)
    mango = pd.read_csv(exam / "clips_mango.csv").fillna({"variant": ""})
    for key, group in mango.groupby(["lang", "split", "variant"]):
        lang, split, variant = key
        block = rating_block(group, scores, with_system=False)
        for result in block.values():
            # MUSHRA 0-100 against MOS 1-5: MSE means nothing
            result.pop("utt_mse", None)
        results["rating_exams"][f"mango/{lang}/{split}/{variant}"] = block

    pairs = pd.read_csv(exam / "pairs_speechjudge.csv")
    add_score_columns(pairs, scores)
    subsets = {
        "all": pairs,
        "sentence_disjoint": pairs[~pairs["sentence_in_train"]],
        "mixed_zh_en": pairs[pairs["lang"] == "zh-en"],
    }
    for name, d in subsets.items():
        d = d[d["label"].isin(["A", "B"])]
        result = {"n": len(d), "always_B": round(float((d["label"] == "B").mean()), 4)}
        result.update(accuracies(d, scores))
        results["speechjudge"][name] = result

    votes = pd.read_csv(exam / "votes_speecharena.csv")
    add_score_columns(votes, scores)
    ok = votes[votes["audio_status"] == "ok"]
    decided = ok[ok["label"].isin(["A", "B"])].copy()
    pairings = []
    for system_a, system_b in zip(decided["system_a"], decided["system_b"]):
        pairings.append(" vs ".join(sorted([system_a, system_b])))
    decided["pairing"] = pairings
    ties = ok[ok["label"] == "TIE"]
    assert len(decided) + len(ties) == len(ok), "every vote with audio is A, B or TIE"

    missing = votes["audio_status"] != "ok"
    block = {
        "n_votes": len(votes),
        "n_audio_missing": len(votes) - len(ok),
        "n_audio_missing_decided": int((missing & votes["label"].isin(["A", "B"])).sum()),
    }
    vote_subsets = {"decided_votes": decided, "decided_votes_mixed": decided[decided["mixed"]]}
    for name, d in vote_subsets.items():
        result = {
            "n": len(d),
            "always_first": round(float((d["label"] == "A").mean()), 4),
            "stronger_system_oracle": round(stronger_system_oracle(d), 4),
        }
        result.update(accuracies(d, scores))
        block[name] = result
    block["decided_votes"]["agreement_across_syntheses"] = AGREEMENT_ACROSS_SYNTHESES

    per_pairing = {}
    for pairing, d in decided.groupby("pairing"):
        result = {"n": len(d)}
        result.update(accuracies(d, scores))
        per_pairing[pairing] = result
    block["per_pairing"] = per_pairing

    macro = {}
    for scorer in scores:
        values = [result[scorer] for result in per_pairing.values()]
        # sum() on purpose, so floats add up exactly as before (Python 3.12+ sums floats more precisely than +=)
        macro[scorer] = round(sum(values) / len(per_pairing), 4)
    block["macro_over_pairings"] = macro

    tie_check = {}
    for scorer in scores:
        gaps = {"decided": mean_abs_gap(decided, scorer)}
        for tie_kind, group in ties.groupby("tie_kind"):
            gaps[f"tie_{tie_kind}"] = mean_abs_gap(group, scorer)
        tie_check[scorer] = gaps
    block["tie_check_mean_abs_gap"] = tie_check
    results["speecharena"] = block
    return results


def markdown_report(results):
    """The results as markdown tables (a list of lines)."""
    scorers = results["scorers"]
    lines = [
        "# Step 2 baseline results",
        "",
        "## Rating exams (utterance SRCC; system SRCC where shown)",
        "",
        "| Exam | " + " | ".join(scorers) + " |",
        "|---|" + "---|" * len(scorers),
    ]
    for exam_name, block in results["rating_exams"].items():
        cells = []
        for scorer in scorers:
            result = block.get(scorer, {})
            text = f"{result.get('utt_srcc', float('nan')):.3f}"
            if "sys_srcc" in result:
                text += f" / {result['sys_srcc']:.3f}"
            if result.get("n_score_failed"):
                text += f" (n={result['n']})"
            cells.append(text)
        lines.append(f"| {exam_name} | " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Pair exams (pairwise accuracy)")
    lines.append("")
    lines.append("| Exam | n | baseline | " + " | ".join(scorers) + " |")
    lines.append("|---|---|---|" + "---|" * len(scorers))
    for name, result in results["speechjudge"].items():
        cells = [table_cell(result, scorer, result["n"]) for scorer in scorers]
        lines.append(f"| SpeechJudge {name} | {result['n']} | always-B {result['always_B']:.3f} | " + " | ".join(cells) + " |")

    arena = results["speecharena"]
    for name in ["decided_votes", "decided_votes_mixed"]:
        result = arena[name]
        agreement = ""
        if "agreement_across_syntheses" in result:
            agreement = f", agreement {result['agreement_across_syntheses']:.3f}"
        baseline = f"first {result['always_first']:.3f}, oracle {result['stronger_system_oracle']:.3f}{agreement}"
        cells = [table_cell(result, scorer, result["n"]) for scorer in scorers]
        lines.append(f"| SAB {name} | {result['n']} | {baseline} | " + " | ".join(cells) + " |")
    macro_cells = [f"{arena['macro_over_pairings'][scorer]:.3f}" for scorer in scorers]
    lines.append("| SAB macro over 6 pairings (main number) | | | " + " | ".join(macro_cells) + " |")

    lines.append("")
    lines.append("### SAB per pairing")
    lines.append("")
    lines.append("| Pairing | n | " + " | ".join(scorers) + " |")
    lines.append("|---|---|" + "---|" * len(scorers))
    for pairing, result in arena["per_pairing"].items():
        cells = [table_cell(result, scorer, result["n"]) for scorer in scorers]
        lines.append(f"| {pairing} | {result['n']} | " + " | ".join(cells) + " |")

    lines.append("")
    lines.append(f"SAB votes: {arena['n_votes']} in total; {arena['n_audio_missing']} have no audio in the released data "
                 f"({arena['n_audio_missing_decided']} of them decided) and are excluded. 'agreement' = how often two raters picked "
                 "the same winner while hearing different syntheses; it is not a human ceiling.")
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--scores", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.root).expanduser()
    out = Path(args.out).expanduser()

    results = evaluate(root / "_exam", load_scores(args.scores))
    out.mkdir(parents=True, exist_ok=True)
    files.save_text(out / "results.json", json.dumps(results, indent=2, default=str))
    lines = markdown_report(results)
    files.save_text(out / "results.md", "\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
