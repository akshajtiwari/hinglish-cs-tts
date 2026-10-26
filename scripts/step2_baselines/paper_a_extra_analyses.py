"""Extra SpeechArenaBench analyses asked for by the Paper A review (26 Oct), from the saved judge scores only.

No audio, no GPU, no new judge scoring. Same votes and credits as the 15 Oct failure analysis.

1. Within-pairing AUC: inside each pairing, how well the judge's score difference (first system minus second, by
   name) separates votes the first system won from votes it lost; 0.5 is chance, ties count half. Averaged over the
   pairings. Unlike winner-balanced accuracy it does not depend on where zero falls, so a judge with a constant
   preference for one system can still show it orders the votes well.
2. Rater reference: two different raters' votes on the same item (same sentence and pairing, but each heard its own
   synthesis). One vote is used to "predict" the other, scored with the same measures as the judges.
3. Judge-implied system order: in each pairing, always pick the system with the higher mean judge score.
4. Hinglish against Hindi-only votes on winner-balanced accuracy and AUC, with the difference and its interval.
5. "Pick the longer clip" as an extra rule, scored like a judge (clip length from the 15 Oct audio features).
6. Holm correction over a declared family of 12 primary tests: winner-balanced accuracy against 50% and AUC against
   0.5 for each judge, and the Hinglish minus Hindi-only winner-balanced difference for each judge.

Intervals: paired sentence-cluster percentile bootstrap, 2,000 draws, seed 15, as in the 15 Oct analysis. Two-sided
bootstrap p-value = 2 x the smaller share of draws on either side of the null value. Exploratory: the test set was
already inspected.

Run from the project folder (laptop, pyenv venv with numpy):
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python \
      scripts/step2_baselines/paper_a_extra_analyses.py \
      --inputs docs/ledger/artifacts/failure_analysis_20261015/inputs \
      --features docs/ledger/artifacts/failure_analysis_20261015/evidence/audio_features.csv \
      --out docs/ledger/artifacts/paper_a_extra_20261026
"""
import argparse
from pathlib import Path

import numpy

from switchmos import files
from analyze_judge_failures import JUDGES, group_by, read_csv
from winner_balanced_intervals import load_votes

ROUNDS = 2000
SEED = 15
RULES = JUDGES + ["longer_clip"]


def add_length_rule(votes, features_path):
    """Give every vote a 'longer_clip' score pair (seconds) and credit, like a judge."""
    seconds = {}
    for row in read_csv(features_path):
        seconds[row["path"]] = float(row["seconds"])
    for row in votes:
        a = seconds[row["path_a"]]
        b = seconds[row["path_b"]]
        row["longer_clip_a"] = a
        row["longer_clip_b"] = b
        if a == b:
            row["longer_clip_credit"] = 0.5
        elif (a > b) == (row["label"] == "A"):
            row["longer_clip_credit"] = 1.0
        else:
            row["longer_clip_credit"] = 0.0


def first_minus_second(row, rule):
    """Score of the pairing's first system (by name) minus the score of its second system."""
    first_system = row["pairing"].split(" vs ")[0]
    if row["system_a"] == first_system:
        return row[rule + "_a"] - row[rule + "_b"]
    return row[rule + "_b"] - row[rule + "_a"]


def first_won(row):
    """True when the pairing's first system (by name) won this vote."""
    return row["winner"] == row["pairing"].split(" vs ")[0]


class PairingData:
    """Everything one pairing needs for fast bootstrap draws: which sentence each vote belongs to, and for every
    rule the credit of each vote and the AUC comparison matrix between first-won and second-won votes."""

    def __init__(self, rows, sentence_index):
        self.won = []
        self.lost = []
        for row in rows:
            if first_won(row):
                self.won.append(row)
            else:
                self.lost.append(row)
        self.won_sentences = numpy.array([sentence_index[row["sentence_id"]] for row in self.won])
        self.lost_sentences = numpy.array([sentence_index[row["sentence_id"]] for row in self.lost])
        self.won_credit = {}
        self.lost_credit = {}
        self.compare = {}
        for rule in RULES:
            self.won_credit[rule] = numpy.array([row[rule + "_credit"] for row in self.won])
            self.lost_credit[rule] = numpy.array([row[rule + "_credit"] for row in self.lost])
            won_diff = numpy.array([first_minus_second(row, rule) for row in self.won])
            lost_diff = numpy.array([first_minus_second(row, rule) for row in self.lost])
            # 1 when a first-won vote has the larger difference, 0.5 for equal, 0 otherwise
            greater = (won_diff[:, None] > lost_diff[None, :]).astype(float)
            equal = (won_diff[:, None] == lost_diff[None, :]).astype(float)
            self.compare[rule] = greater + 0.5 * equal

    def measures(self, rule, weights):
        """(winner-balanced accuracy, AUC) for one rule, each vote weighted by how often its sentence was drawn."""
        w_won = weights[self.won_sentences]
        w_lost = weights[self.lost_sentences]
        if w_won.sum() == 0 or w_lost.sum() == 0:
            return None, None
        balanced = 0.5 * ((w_won * self.won_credit[rule]).sum() / w_won.sum()
                          + (w_lost * self.lost_credit[rule]).sum() / w_lost.sum())
        auc = (w_won @ self.compare[rule] @ w_lost) / (w_won.sum() * w_lost.sum())
        return balanced, auc


def subset_measures(pairings, weights):
    """{rule: (mean winner-balanced accuracy, mean AUC)} over pairings, or None if a pairing lost one side."""
    result = {}
    for rule in RULES:
        balanced_values = []
        auc_values = []
        for data in pairings:
            balanced, auc = data.measures(rule, weights)
            if balanced is None:
                return None
            balanced_values.append(balanced)
            auc_values.append(auc)
        result[rule] = (float(numpy.mean(balanced_values)), float(numpy.mean(auc_values)))
    return result


def build_pairings(rows, sentence_index):
    """PairingData for every pairing in which both systems win at least one vote."""
    pairings = []
    for pairing, group in sorted(group_by(rows, "pairing").items()):
        if len(group_by(group, "winner")) == 2:
            pairings.append(PairingData(group, sentence_index))
    return pairings


def rater_reference(votes):
    """Every ordered pair of two decided votes on the same item by different raters: (predicting vote, predicted vote)."""
    pairs = []
    for item, group in group_by(votes, "pair_id").items():
        for u in group:
            for v in group:
                if u["vote_id"] != v["vote_id"] and u["rater_id"] != v["rater_id"]:
                    pairs.append((u, v))
    return pairs


def rater_measures(pairs, weights, sentence_index):
    """Agreement, and winner-balanced accuracy over pairings, when one rater's vote predicts the other's."""
    per_pairing = {}
    total = 0.0
    agree = 0.0
    for u, v in pairs:
        w = weights[sentence_index[v["sentence_id"]]]
        if w == 0:
            continue
        hit = float(u["winner"] == v["winner"])
        total += w
        agree += w * hit
        side = "won" if first_won(v) else "lost"
        block = per_pairing.setdefault(v["pairing"], {"won": [0.0, 0.0], "lost": [0.0, 0.0]})
        block[side][0] += w * hit
        block[side][1] += w
    balanced = []
    for block in per_pairing.values():
        if block["won"][1] == 0 or block["lost"][1] == 0:
            return None, None
        balanced.append(0.5 * (block["won"][0] / block["won"][1] + block["lost"][0] / block["lost"][1]))
    return agree / total, float(numpy.mean(balanced))


def implied_order_accuracy(rows, rule):
    """Accuracy of always picking, in each pairing, the system with the higher mean score of this rule."""
    means = {}
    counts = {}
    for row in rows:
        for side in ["a", "b"]:
            system = row["system_" + side]
            means[system] = means.get(system, 0.0) + row[rule + "_" + side]
            counts[system] = counts.get(system, 0) + 1
    for system in means:
        means[system] = means[system] / counts[system]
    right = 0
    for row in rows:
        first, second = row["pairing"].split(" vs ")
        pick = first if means[first] >= means[second] else second
        right += int(pick == row["winner"])
    return right / len(rows), means


def interval(values):
    """95% percentile interval of a list of bootstrap values."""
    low, high = numpy.quantile(numpy.array(values), [0.025, 0.975])
    return [float(low), float(high)]


def two_sided_p(values, null):
    """Two-sided bootstrap p-value of a statistic against a null value."""
    values = numpy.array(values)
    below = numpy.mean(values <= null)
    above = numpy.mean(values >= null)
    return float(min(1.0, 2 * min(below, above)))


def holm(p_values):
    """Holm-adjusted p-values, same order as given."""
    ranked = []
    for index in range(len(p_values)):
        ranked.append((p_values[index], index))
    ranked.sort()
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank in range(len(ranked)):
        index = ranked[rank][1]
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[index]))
        adjusted[index] = running
    return adjusted


def main():
    parser = argparse.ArgumentParser(description="Extra SAB analyses for the Paper A review.")
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    votes = load_votes(args.inputs)
    add_length_rule(votes, args.features)
    sentences = sorted(group_by(votes, "sentence_id"))
    sentence_index = {}
    for i, sentence in enumerate(sentences):
        sentence_index[sentence] = i
    subsets = {"all": votes, "hinglish": [], "hindi_only": []}
    for row in votes:
        if row["mixed"]:
            subsets["hinglish"].append(row)
        else:
            subsets["hindi_only"].append(row)
    pairings = {}
    for name, rows in subsets.items():
        pairings[name] = build_pairings(rows, sentence_index)
    rater_pairs = rater_reference(votes)

    # point estimates: every sentence counted once
    ones = numpy.ones(len(sentences))
    report = {"exploratory": True, "rounds": ROUNDS, "seed": SEED, "votes": len(votes), "sentences": len(sentences),
              "rater_pairs_ordered": len(rater_pairs), "subsets": {}, "implied_order": {}, "rater_reference": {}}
    for name in subsets:
        point = subset_measures(pairings[name], ones)
        report["subsets"][name] = {"votes": len(subsets[name]), "pairings": len(pairings[name]), "rules": {}}
        for rule in RULES:
            report["subsets"][name]["rules"][rule] = {"winner_balanced": point[rule][0], "auc": point[rule][1]}
    agreement, rater_balanced = rater_measures(rater_pairs, ones, sentence_index)
    report["rater_reference"] = {"agreement": agreement, "winner_balanced": rater_balanced}
    for rule in RULES:
        accuracy, means = implied_order_accuracy(votes, rule)
        report["implied_order"][rule] = {"accuracy": accuracy, "system_means": means}

    # bootstrap: the same sentence draw for every subset, rule and the rater reference
    rng = numpy.random.default_rng(SEED)
    draws = {"all": [], "hinglish": [], "hindi_only": [], "rater": []}
    for draw_number in range(ROUNDS):
        picked = rng.integers(0, len(sentences), size=len(sentences))
        weights = numpy.bincount(picked, minlength=len(sentences)).astype(float)
        results = {}
        for name in subsets:
            results[name] = subset_measures(pairings[name], weights)
        rater = rater_measures(rater_pairs, weights, sentence_index)
        if None in results.values() or rater[1] is None:
            continue
        for name in subsets:
            draws[name].append(results[name])
        draws["rater"].append(rater)
    report["draws_kept"] = len(draws["rater"])

    tests = []
    for name in subsets:
        for rule in RULES:
            block = report["subsets"][name]["rules"][rule]
            balanced_values = [d[rule][0] for d in draws[name]]
            auc_values = [d[rule][1] for d in draws[name]]
            block["winner_balanced_ci95"] = interval(balanced_values)
            block["auc_ci95"] = interval(auc_values)
            block["winner_balanced_p_vs_half"] = two_sided_p(balanced_values, 0.5)
            block["auc_p_vs_half"] = two_sided_p(auc_values, 0.5)
            if name == "all" and rule in JUDGES:
                tests.append({"test": f"{rule} winner-balanced vs 0.5 (all votes)", "p": block["winner_balanced_p_vs_half"]})
                tests.append({"test": f"{rule} AUC vs 0.5 (all votes)", "p": block["auc_p_vs_half"]})
    report["hinglish_minus_hindi_only"] = {}
    for rule in RULES:
        balanced_diff = []
        auc_diff = []
        for mixed, single in zip(draws["hinglish"], draws["hindi_only"]):
            balanced_diff.append(mixed[rule][0] - single[rule][0])
            auc_diff.append(mixed[rule][1] - single[rule][1])
        mixed_point = report["subsets"]["hinglish"]["rules"][rule]
        single_point = report["subsets"]["hindi_only"]["rules"][rule]
        block = {"winner_balanced": mixed_point["winner_balanced"] - single_point["winner_balanced"],
                 "winner_balanced_ci95": interval(balanced_diff),
                 "winner_balanced_p_vs_zero": two_sided_p(balanced_diff, 0.0),
                 "auc": mixed_point["auc"] - single_point["auc"], "auc_ci95": interval(auc_diff)}
        report["hinglish_minus_hindi_only"][rule] = block
        if rule in JUDGES:
            tests.append({"test": f"{rule} Hinglish minus Hindi-only winner-balanced", "p": block["winner_balanced_p_vs_zero"]})
    report["rater_reference"]["agreement_ci95"] = interval([d[0] for d in draws["rater"]])
    report["rater_reference"]["winner_balanced_ci95"] = interval([d[1] for d in draws["rater"]])

    adjusted = holm([test["p"] for test in tests])
    for test, p_holm in zip(tests, adjusted):
        test["p_holm"] = p_holm
    report["holm_family"] = tests

    args.out.mkdir(parents=True, exist_ok=True)
    files.save_json(args.out / "paper_a_extra.json", report)
    print(f"votes {len(votes)}, sentences {len(sentences)}, ordered rater pairs {len(rater_pairs)}, draws kept {report['draws_kept']}")
    for name in subsets:
        for rule in RULES:
            block = report["subsets"][name]["rules"][rule]
            print(f"{name:10s} {rule:11s} WBA {100 * block['winner_balanced']:.1f} "
                  f"[{100 * block['winner_balanced_ci95'][0]:.1f}, {100 * block['winner_balanced_ci95'][1]:.1f}]  "
                  f"AUC {block['auc']:.3f} [{block['auc_ci95'][0]:.3f}, {block['auc_ci95'][1]:.3f}]")
    rater = report["rater_reference"]
    print(f"rater reference: agreement {100 * rater['agreement']:.1f}, WBA {100 * rater['winner_balanced']:.1f} "
          f"[{100 * rater['winner_balanced_ci95'][0]:.1f}, {100 * rater['winner_balanced_ci95'][1]:.1f}]")
    for rule in RULES:
        print(f"implied system order {rule}: {100 * report['implied_order'][rule]['accuracy']:.1f}")
    for test in tests:
        print(f"{test['test']}: p {test['p']:.4f}, Holm {test['p_holm']:.4f}")


if __name__ == "__main__":
    main()
