"""The system-vs-clip split of judge accuracy on any table of pairwise votes, from saved judge scores only.

First written for the Paper A review on SpeechArenaBench Hindi (26 Oct, L-0125); since 14 Nov it runs on any votes
table in the SAB votes format (Kannada, Marathi, TTS-HP, MANGO pages; docs/plan/21_paper_a_generalisation_prereg.md).
No audio, no GPU, no new judge scoring.

For every rule (each judge, plus feature rules such as "pick the longer clip" or "pick the louder clip"):
1. Plain accuracy on decided votes, and the stronger-system rule: in each pairing, always pick the system that won
   more of the votes. The difference between a judge and that rule is tested.
2. Winner-balanced accuracy: inside each pairing, accuracy on the votes won by one system and on the votes won by the
   other are averaged, then the pairings are averaged. Any rule that always picks one system gets exactly 50%.
3. Within-pairing AUC: inside each pairing, how well the score difference (first system minus second, by name)
   separates votes the first system won from votes it lost; 0.5 is chance, ties count half.
4. Rater reference (only when two different raters voted on the same item): one vote "predicts" the other.
5. Judge-implied system order: in each pairing, always pick the system with the higher mean score of the rule.
6. With --subset-column: the same measures on the rows where that column is True and where it is False, and the
   difference (for SAB, code-mixed against single-language votes).
7. Each judge minus each feature rule (winner-balanced accuracy and AUC), paired on the same draws; descriptive.
8. Holm correction over the declared family: for each judge, winner-balanced vs 50%, AUC vs 0.5 and accuracy minus
   the stronger-system rule vs 0; plus, with --subset-column, the True minus False winner-balanced difference.

Intervals: paired sentence-cluster percentile bootstrap, 2,000 draws, seed 15. A draw is kept only if every pairing of
every subset still has votes won by each of its two systems (and the rater reference, when used, can be computed).
Two-sided bootstrap p-value = 2 x the smaller share of draws on either side of the null value.

Run from the project folder (laptop venv with numpy), for example the Hindi votes with both feature rules:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python \\
      scripts/step2_baselines/paper_a_extra_analyses.py \\
      --votes docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/votes_speecharena.csv \\
      --scores docs/ledger/artifacts/failure_analysis_20261015/inputs/scores \\
      --features docs/ledger/artifacts/failure_analysis_20261015/evidence/audio_features.csv \\
      --feature-rules seconds:longer_clip,rms:louder_clip --subset-column mixed \\
      --name sab_hi --out docs/ledger/artifacts/generalisation_<date>
"""
import argparse
import math
from pathlib import Path

import numpy

from switchmos import files
from analyze_judge_failures import JUDGES, group_by, join_scores, read_csv

ROUNDS = 2000
SEED = 15


def load_votes(votes_path, scores_dir, judges):
    """Decided votes with audio, with every judge's two scores and credit (equal scores count half)."""
    scores = {}
    for judge in judges:
        lookup = {}
        for row in read_csv(Path(scores_dir) / (judge + ".csv")):
            lookup[row["path"]] = float(row["score"])
            assert math.isfinite(lookup[row["path"]]), "Non-finite score"
        scores[judge] = lookup
    return join_scores(read_csv(votes_path), scores, True, judges)


def add_feature_rule(votes, features_path, field, rule):
    """Give every vote a score pair and credit for the rule "pick the clip with the larger value of field"."""
    values = {}
    for row in read_csv(features_path):
        values[row["path"]] = float(row[field])
    for row in votes:
        a = values[row["path_a"]]
        b = values[row["path_b"]]
        row[rule + "_a"] = a
        row[rule + "_b"] = b
        if a == b:
            row[rule + "_credit"] = 0.5
        elif (a > b) == (row["label"] == "A"):
            row[rule + "_credit"] = 1.0
        else:
            row[rule + "_credit"] = 0.0


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

    def __init__(self, rows, sentence_index, rules):
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
        for rule in rules:
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


class VoteArrays:
    """Plain accuracy of every rule, and of the stronger-system rule, over all votes of one subset, for any draw."""

    def __init__(self, rows, sentence_index, rules):
        pairing_names = sorted(group_by(rows, "pairing"))
        pairing_code = {}
        for code, name in enumerate(pairing_names):
            pairing_code[name] = code
        self.n_pairings = len(pairing_names)
        self.sentences = numpy.array([sentence_index[row["sentence_id"]] for row in rows])
        self.pairings = numpy.array([pairing_code[row["pairing"]] for row in rows])
        self.first_won = numpy.array([float(first_won(row)) for row in rows])
        self.credit = {}
        for rule in rules:
            self.credit[rule] = numpy.array([row[rule + "_credit"] for row in rows])

    def accuracy(self, rule, weights):
        """Share of (weighted) votes the rule gets right, or None when no vote has weight."""
        w = weights[self.sentences]
        if w.sum() == 0:
            return None
        return float((w * self.credit[rule]).sum() / w.sum())

    def stronger_system(self, weights):
        """Accuracy of picking, in each pairing, the system that won more of the (weighted) votes."""
        w = weights[self.sentences]
        if w.sum() == 0:
            return None
        won = numpy.bincount(self.pairings, weights=w * self.first_won, minlength=self.n_pairings)
        lost = numpy.bincount(self.pairings, weights=w * (1 - self.first_won), minlength=self.n_pairings)
        return float(numpy.maximum(won, lost).sum() / w.sum())


def subset_measures(pairings, weights, rules):
    """{rule: (mean winner-balanced accuracy, mean AUC)} over pairings, or None if a pairing lost one side."""
    result = {}
    for rule in rules:
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


def plain_measures(arrays, weights, rules):
    """{rule: accuracy} plus the stronger-system rule under "stronger_system", or None when nothing has weight."""
    result = {"stronger_system": arrays.stronger_system(weights)}
    if result["stronger_system"] is None:
        return None
    for rule in rules:
        result[rule] = arrays.accuracy(rule, weights)
    return result


def build_pairings(rows, sentence_index, rules):
    """PairingData for every pairing in which both systems win at least one vote."""
    pairings = []
    for pairing, group in sorted(group_by(rows, "pairing").items()):
        if len(group_by(group, "winner")) == 2:
            pairings.append(PairingData(group, sentence_index, rules))
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
    """Agreement, and winner-balanced accuracy over pairings, when one rater's vote predicts the other's.
    (None, None) when there are no such pairs or no pair has weight in this draw."""
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
    if total == 0:
        return None, None
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


def is_true(value):
    """A subset column value read from a csv ("True"/"False") or already a bool."""
    if isinstance(value, bool):
        return value
    return value == "True"


def make_subsets(votes, column):
    """{"all": votes} and, with a column, {column: rows where it is True, "not_" + column: rows where it is False}."""
    subsets = {"all": votes}
    if column:
        subsets[column] = []
        subsets["not_" + column] = []
        for row in votes:
            if is_true(row[column]):
                subsets[column].append(row)
            else:
                subsets["not_" + column].append(row)
    return subsets


def parse_feature_rules(text):
    """"seconds:longer_clip,rms:louder_clip" -> [("seconds", "longer_clip"), ("rms", "louder_clip")]."""
    rules = []
    if text:
        for part in text.split(","):
            field, rule = part.split(":")
            rules.append((field, rule))
    return rules


def analyse(votes, judges, rules, column):
    """The full report for one votes table (rows already carry <rule>_a, <rule>_b and <rule>_credit)."""
    sentences = sorted(group_by(votes, "sentence_id"))
    sentence_index = {}
    for i, sentence in enumerate(sentences):
        sentence_index[sentence] = i
    subsets = make_subsets(votes, column)
    pairings = {}
    arrays = {}
    for name, rows in subsets.items():
        pairings[name] = build_pairings(rows, sentence_index, rules)
        arrays[name] = VoteArrays(rows, sentence_index, rules)
        if not pairings[name]:
            raise ValueError(f"subset {name!r} has no pairing in which both systems win; leave out --subset-column")
    # the rater reference uses the same pairings as winner-balanced accuracy: those both systems win at least once
    balanced = set()
    for pairing, group in group_by(votes, "pairing").items():
        if len(group_by(group, "winner")) == 2:
            balanced.add(pairing)
    rater_pairs = []
    for u, v in rater_reference(votes):
        if v["pairing"] in balanced:
            rater_pairs.append((u, v))
    use_rater = len(rater_pairs) > 0

    # point estimates: every sentence counted once
    ones = numpy.ones(len(sentences))
    report = {"rounds": ROUNDS, "seed": SEED, "votes": len(votes), "sentences": len(sentences), "judges": judges,
              "rules": rules, "subset_column": column, "rater_pairs_ordered": len(rater_pairs), "subsets": {},
              "implied_order": {}, "rater_reference": None}
    for name in subsets:
        point = subset_measures(pairings[name], ones, rules)
        plain = plain_measures(arrays[name], ones, rules)
        kept_votes = 0
        for data in pairings[name]:
            kept_votes += len(data.won) + len(data.lost)
        block = {"votes": len(subsets[name]), "pairings": len(pairings[name]), "votes_in_balanced_pairings": kept_votes,
                 "stronger_system": plain["stronger_system"], "rules": {}}
        for rule in rules:
            block["rules"][rule] = {"accuracy": plain[rule], "winner_balanced": point[rule][0], "auc": point[rule][1]}
        report["subsets"][name] = block
    if use_rater:
        agreement, rater_balanced = rater_measures(rater_pairs, ones, sentence_index)
        report["rater_reference"] = {"agreement": agreement, "winner_balanced": rater_balanced}
    for rule in rules:
        accuracy, means = implied_order_accuracy(votes, rule)
        report["implied_order"][rule] = {"accuracy": accuracy, "system_means": means}

    # bootstrap: the same sentence draw for every subset, rule and the rater reference
    rng = numpy.random.default_rng(SEED)
    draws = {"rater": []}
    plain_draws = {}
    for name in subsets:
        draws[name] = []
        plain_draws[name] = []
    for draw_number in range(ROUNDS):
        picked = rng.integers(0, len(sentences), size=len(sentences))
        weights = numpy.bincount(picked, minlength=len(sentences)).astype(float)
        results = {}
        plain_results = {}
        for name in subsets:
            results[name] = subset_measures(pairings[name], weights, rules)
            plain_results[name] = plain_measures(arrays[name], weights, rules)
        rater = (None, None)
        if use_rater:
            rater = rater_measures(rater_pairs, weights, sentence_index)
        if None in results.values() or None in plain_results.values() or (use_rater and rater[1] is None):
            continue
        for name in subsets:
            draws[name].append(results[name])
            plain_draws[name].append(plain_results[name])
        draws["rater"].append(rater)
    report["draws_kept"] = len(draws["all"])

    tests = []
    for name in subsets:
        block = report["subsets"][name]
        block["stronger_system_ci95"] = interval([d["stronger_system"] for d in plain_draws[name]])
        for rule in rules:
            rule_block = block["rules"][rule]
            balanced_values = [d[rule][0] for d in draws[name]]
            auc_values = [d[rule][1] for d in draws[name]]
            accuracy_values = [d[rule] for d in plain_draws[name]]
            gap_values = [d[rule] - d["stronger_system"] for d in plain_draws[name]]
            rule_block["winner_balanced_ci95"] = interval(balanced_values)
            rule_block["auc_ci95"] = interval(auc_values)
            rule_block["winner_balanced_p_vs_half"] = two_sided_p(balanced_values, 0.5)
            rule_block["auc_p_vs_half"] = two_sided_p(auc_values, 0.5)
            rule_block["accuracy_ci95"] = interval(accuracy_values)
            rule_block["minus_stronger_system"] = rule_block["accuracy"] - block["stronger_system"]
            rule_block["minus_stronger_system_ci95"] = interval(gap_values)
            rule_block["minus_stronger_system_p_vs_zero"] = two_sided_p(gap_values, 0.0)
            if name == "all" and rule in judges:
                tests.append({"test": f"{rule} winner-balanced vs 0.5 (all votes)", "p": rule_block["winner_balanced_p_vs_half"]})
                tests.append({"test": f"{rule} AUC vs 0.5 (all votes)", "p": rule_block["auc_p_vs_half"]})
                tests.append({"test": f"{rule} accuracy minus stronger-system rule (all votes)",
                              "p": rule_block["minus_stronger_system_p_vs_zero"]})
    if column:
        difference_name = column + "_minus_not_" + column
        report[difference_name] = {}
        for rule in rules:
            balanced_diff = []
            auc_diff = []
            for true_draw, false_draw in zip(draws[column], draws["not_" + column]):
                balanced_diff.append(true_draw[rule][0] - false_draw[rule][0])
                auc_diff.append(true_draw[rule][1] - false_draw[rule][1])
            true_point = report["subsets"][column]["rules"][rule]
            false_point = report["subsets"]["not_" + column]["rules"][rule]
            block = {"winner_balanced": true_point["winner_balanced"] - false_point["winner_balanced"],
                     "winner_balanced_ci95": interval(balanced_diff),
                     "winner_balanced_p_vs_zero": two_sided_p(balanced_diff, 0.0),
                     "auc": true_point["auc"] - false_point["auc"], "auc_ci95": interval(auc_diff)}
            report[difference_name][rule] = block
            if rule in judges:
                tests.append({"test": f"{rule} {column} minus not {column} winner-balanced",
                              "p": block["winner_balanced_p_vs_zero"]})
    # each judge against each feature rule on the same draws (descriptive, outside the Holm family)
    report["judge_minus_feature_rule"] = {}
    point = report["subsets"]["all"]["rules"]
    for judge in judges:
        for rule in rules:
            if rule in judges:
                continue
            balanced_diff = [d[judge][0] - d[rule][0] for d in draws["all"]]
            auc_diff = [d[judge][1] - d[rule][1] for d in draws["all"]]
            report["judge_minus_feature_rule"][judge + " minus " + rule] = {
                "winner_balanced": point[judge]["winner_balanced"] - point[rule]["winner_balanced"],
                "winner_balanced_ci95": interval(balanced_diff),
                "winner_balanced_p_vs_zero": two_sided_p(balanced_diff, 0.0),
                "auc": point[judge]["auc"] - point[rule]["auc"],
                "auc_ci95": interval(auc_diff),
                "auc_p_vs_zero": two_sided_p(auc_diff, 0.0)}
    if use_rater:
        report["rater_reference"]["agreement_ci95"] = interval([d[0] for d in draws["rater"]])
        report["rater_reference"]["winner_balanced_ci95"] = interval([d[1] for d in draws["rater"]])

    adjusted = holm([test["p"] for test in tests])
    for test, p_holm in zip(tests, adjusted):
        test["p_holm"] = p_holm
    report["holm_family"] = tests
    return report


def main():
    parser = argparse.ArgumentParser(description="System-vs-clip split of judge accuracy on a votes table.")
    parser.add_argument("--votes", type=Path, required=True, help="votes csv in the SAB votes format")
    parser.add_argument("--scores", type=Path, required=True, help="folder with <judge>.csv (path,score)")
    parser.add_argument("--judges", default=",".join(JUDGES))
    parser.add_argument("--features", type=Path, default=None, help="csv with path and feature columns")
    parser.add_argument("--feature-rules", default="", help="field:rule,... for example seconds:longer_clip")
    parser.add_argument("--subset-column", default="", help="a True/False column, for example mixed")
    parser.add_argument("--name", required=True, help="output file name, for example sab_kn")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    judges = args.judges.split(",")
    feature_rules = parse_feature_rules(args.feature_rules)
    votes = load_votes(args.votes, args.scores, judges)
    rules = list(judges)
    for field, rule in feature_rules:
        add_feature_rule(votes, args.features, field, rule)
        rules.append(rule)

    report = analyse(votes, judges, rules, args.subset_column)
    report["inputs"] = {"votes": str(args.votes), "scores": str(args.scores), "features": str(args.features)}
    args.out.mkdir(parents=True, exist_ok=True)
    files.save_json(args.out / (args.name + ".json"), report)

    print(f"{args.name}: votes {report['votes']}, sentences {report['sentences']}, "
          f"ordered rater pairs {report['rater_pairs_ordered']}, draws kept {report['draws_kept']}")
    for name, block in report["subsets"].items():
        print(f"{name}: {block['votes']} votes, {block['pairings']} balanced pairings, "
              f"stronger-system rule {100 * block['stronger_system']:.1f}")
        for rule in rules:
            rule_block = block["rules"][rule]
            print(f"  {rule:12s} acc {100 * rule_block['accuracy']:.1f}  WBA {100 * rule_block['winner_balanced']:.1f} "
                  f"[{100 * rule_block['winner_balanced_ci95'][0]:.1f}, {100 * rule_block['winner_balanced_ci95'][1]:.1f}]  "
                  f"AUC {rule_block['auc']:.3f} [{rule_block['auc_ci95'][0]:.3f}, {rule_block['auc_ci95'][1]:.3f}]")
    if report["rater_reference"] is not None:
        rater = report["rater_reference"]
        print(f"rater reference: agreement {100 * rater['agreement']:.1f}, WBA {100 * rater['winner_balanced']:.1f} "
              f"[{100 * rater['winner_balanced_ci95'][0]:.1f}, {100 * rater['winner_balanced_ci95'][1]:.1f}]")
    for rule in rules:
        print(f"implied system order {rule}: {100 * report['implied_order'][rule]['accuracy']:.1f}")
    for name, block in report["judge_minus_feature_rule"].items():
        print(f"{name}: WBA {100 * block['winner_balanced']:+.1f} [{100 * block['winner_balanced_ci95'][0]:+.1f}, "
              f"{100 * block['winner_balanced_ci95'][1]:+.1f}]  AUC {block['auc']:+.3f} "
              f"[{block['auc_ci95'][0]:+.3f}, {block['auc_ci95'][1]:+.3f}]")
    for test in report["holm_family"]:
        print(f"{test['test']}: p {test['p']:.4f}, Holm {test['p_holm']:.4f}")


if __name__ == "__main__":
    main()
