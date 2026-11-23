"""The system-vs-clip split on a rating corpus (BVCC, SOMOS): how much of a judge's clip-level correlation is system.

From saved judge scores only. Fixed in docs/plan/21_paper_a_generalisation_prereg.md:
- Clips used: audio present, from systems with at least --min-clips such clips (4).
- Clip SRCC: Spearman between judge score and MOS over all used clips (what papers usually report).
- System rule: every clip gets the mean MOS of the other clips of its system (leave-one-out), so it knows only which
  system made the clip. Its clip SRCC shows how much of the clip-level ranking system identity alone explains.
- Within-system SRCC: Spearman between judge score and MOS inside each system, averaged over systems (equal
  weight). Systems where either list is constant are skipped and counted.
- With --pairs (SOMOS): two clips of the same sentence from different systems make a pair; the label is the clip with
  the higher MOS, kept when the MOS difference is at least --pair-gap (and not zero). Accuracy of each judge and of
  the system rule (higher leave-one-out system mean; equal means count half), and each judge's accuracy on the pairs
  the system rule gets right and on those it gets wrong.
Intervals: percentile bootstrap, 2,000 draws, seed 15; systems are resampled for the correlations and sentences for
the pairs.

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python scripts/step2_baselines/within_system.py \\
      --clips docs/server_mirror/hinglish-cs-tts/datasets/_exam/clips_somos.csv \\
      --scores docs/ledger/artifacts/failure_analysis_20261015/inputs/scores --pairs --pair-gap 0.5 \\
      --name somos --out docs/ledger/artifacts/generalisation_<date>
"""
import argparse
import math
from pathlib import Path

import numpy

from switchmos import files
from switchmos.eval.metrics import spearman
from analyze_judge_failures import JUDGES, credit, group_by, read_csv
from paper_a_extra_analyses import interval

ROUNDS = 2000
SEED = 15


def load_clips(clips_path, scores_dir, judges, min_clips):
    """Clips with audio and every judge's score, from systems with at least min_clips such clips."""
    scores = {}
    for judge in judges:
        lookup = {}
        for row in read_csv(Path(scores_dir) / (judge + ".csv")):
            lookup[row["path"]] = float(row["score"])
        scores[judge] = lookup
    clips = []
    for row in read_csv(clips_path):
        if row["audio_status"] != "ok":
            continue
        clip = {"clip_id": row["clip_id"], "system": row["system"], "mos": float(row["mos"])}
        for judge in judges:
            clip[judge] = scores[judge][row["path"]]
        clips.append(clip)
    kept = []
    for system, group in group_by(clips, "system").items():
        if len(group) >= min_clips:
            kept.extend(group)
    return kept


def add_leave_one_out_means(clips):
    """clip["system_rule"] = mean MOS of the other clips of the same system."""
    for system, group in group_by(clips, "system").items():
        total = sum([clip["mos"] for clip in group])
        for clip in group:
            clip["system_rule"] = (total - clip["mos"]) / (len(group) - 1)


def within_system_values(clips, judge):
    """{system: Spearman between judge score and MOS inside that system}, without systems where it is undefined."""
    values = {}
    for system, group in group_by(clips, "system").items():
        value = spearman([clip[judge] for clip in group], [clip["mos"] for clip in group])
        if not math.isnan(value):
            values[system] = value
    return values


def weighted_srcc(clips_by_system, counts, key):
    """Clip-level Spearman with each system's clips repeated as often as the system was drawn."""
    predicted = []
    true = []
    for system, count in counts.items():
        for repeat in range(count):
            for clip in clips_by_system[system]:
                predicted.append(clip[key])
                true.append(clip["mos"])
    return spearman(predicted, true)


def correlation_report(clips, judges):
    """Clip SRCC, system-rule SRCC and within-system SRCC with system-cluster bootstrap intervals."""
    clips_by_system = group_by(clips, "system")
    systems = sorted(clips_by_system)
    within = {}
    for judge in judges:
        within[judge] = within_system_values(clips, judge)
    report = {"clips": len(clips), "systems": len(systems), "system_rule_clip_srcc": None, "judges": {}}
    ones = {}
    for system in systems:
        ones[system] = 1
    report["system_rule_clip_srcc"] = weighted_srcc(clips_by_system, ones, "system_rule")
    for judge in judges:
        values = list(within[judge].values())
        report["judges"][judge] = {"clip_srcc": weighted_srcc(clips_by_system, ones, judge),
                                   "within_system_srcc": sum(values) / len(values),
                                   "within_system_used": len(values),
                                   "within_system_skipped": len(systems) - len(values)}

    rng = numpy.random.default_rng(SEED)
    draws = {"system_rule": []}
    for judge in judges:
        draws[judge] = {"clip": [], "within": [], "difference": []}
    for draw_number in range(ROUNDS):
        picked = rng.integers(0, len(systems), size=len(systems))
        counts = {}
        for index in picked:
            counts[systems[index]] = counts.get(systems[index], 0) + 1
        draws["system_rule"].append(weighted_srcc(clips_by_system, counts, "system_rule"))
        for judge in judges:
            clip_value = weighted_srcc(clips_by_system, counts, judge)
            total = 0.0
            weight = 0
            for system, count in counts.items():
                if system in within[judge]:
                    total += count * within[judge][system]
                    weight += count
            within_value = total / weight
            draws[judge]["clip"].append(clip_value)
            draws[judge]["within"].append(within_value)
            draws[judge]["difference"].append(clip_value - within_value)
    report["system_rule_clip_srcc_ci95"] = interval(draws["system_rule"])
    for judge in judges:
        block = report["judges"][judge]
        block["clip_srcc_ci95"] = interval(draws[judge]["clip"])
        block["within_system_srcc_ci95"] = interval(draws[judge]["within"])
        block["clip_minus_within"] = block["clip_srcc"] - block["within_system_srcc"]
        block["clip_minus_within_ci95"] = interval(draws[judge]["difference"])
    return report


def sentence_of(clip_id):
    """SOMOS clip ids are <sentence>_<system>, for example LJ002-0181_110."""
    return clip_id.rsplit("_", 1)[0]


def same_sentence_pairs(clips, judges, gap):
    """Pairs of clips of the same sentence from different systems, with the credit of every judge and the rule."""
    for clip in clips:
        clip["sentence"] = sentence_of(clip["clip_id"])
    pairs = []
    for sentence, group in sorted(group_by(clips, "sentence").items()):
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group[i]
                b = group[j]
                difference = a["mos"] - b["mos"]
                if difference == 0 or abs(difference) < gap or a["system"] == b["system"]:
                    continue
                label = "A" if difference > 0 else "B"
                pair = {"sentence": sentence, "system_rule": credit(a["system_rule"], b["system_rule"], label)}
                for judge in judges:
                    pair[judge] = credit(a[judge], b[judge], label)
                pairs.append(pair)
    return pairs


def pair_report(pairs, judges):
    """Accuracy of every judge and the system rule, and judge accuracy where the rule is right and where it is wrong."""
    sentences = sorted(group_by(pairs, "sentence"))
    sentence_index = {}
    for i, sentence in enumerate(sentences):
        sentence_index[sentence] = i
    where = numpy.array([sentence_index[pair["sentence"]] for pair in pairs])
    rule = numpy.array([pair["system_rule"] for pair in pairs])
    rule_right = rule == 1.0
    rule_wrong = rule == 0.0
    credits = {}
    for judge in judges:
        credits[judge] = numpy.array([pair[judge] for pair in pairs])

    def measures(weights):
        w = weights[where]
        result = {"system_rule": float((w * rule).sum() / w.sum())}
        for judge in judges:
            result[judge] = float((w * credits[judge]).sum() / w.sum())
            result[judge + "_rule_right"] = float((w * credits[judge] * rule_right).sum() / (w * rule_right).sum())
            result[judge + "_rule_wrong"] = float((w * credits[judge] * rule_wrong).sum() / (w * rule_wrong).sum())
        return result

    report = {"pairs": len(pairs), "sentences": len(sentences), "rule_right": int(rule_right.sum()),
              "rule_wrong": int(rule_wrong.sum()), "point": measures(numpy.ones(len(sentences))), "ci95": {}}
    rng = numpy.random.default_rng(SEED)
    draws = []
    for draw_number in range(ROUNDS):
        picked = rng.integers(0, len(sentences), size=len(sentences))
        weights = numpy.bincount(picked, minlength=len(sentences)).astype(float)
        if (weights[where] * rule_right).sum() == 0 or (weights[where] * rule_wrong).sum() == 0:
            continue
        draws.append(measures(weights))
    report["draws_kept"] = len(draws)
    for key in report["point"]:
        report["ci95"][key] = interval([draw[key] for draw in draws])
    return report


def main():
    parser = argparse.ArgumentParser(description="System-vs-clip split on a rating corpus.")
    parser.add_argument("--clips", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--judges", default=",".join(JUDGES))
    parser.add_argument("--min-clips", type=int, default=4)
    parser.add_argument("--pairs", action="store_true", help="also same-sentence pairs (SOMOS)")
    parser.add_argument("--pair-gap", type=float, default=0.5)
    parser.add_argument("--name", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    judges = args.judges.split(",")
    clips = load_clips(args.clips, args.scores, judges, args.min_clips)
    add_leave_one_out_means(clips)
    report = {"name": args.name, "min_clips": args.min_clips, "rounds": ROUNDS, "seed": SEED,
              "inputs": {"clips": str(args.clips), "scores": str(args.scores)},
              "correlations": correlation_report(clips, judges)}
    if args.pairs:
        report["pair_gap"] = args.pair_gap
        report["pairs"] = pair_report(same_sentence_pairs(clips, judges, args.pair_gap), judges)
    args.out.mkdir(parents=True, exist_ok=True)
    files.save_json(args.out / (args.name + ".json"), report)

    block = report["correlations"]
    print(f"{args.name}: {block['clips']} clips, {block['systems']} systems; "
          f"system rule clip SRCC {block['system_rule_clip_srcc']:.3f}")
    for judge in judges:
        values = block["judges"][judge]
        print(f"  {judge:11s} clip SRCC {values['clip_srcc']:.3f}  within-system {values['within_system_srcc']:.3f} "
              f"({values['within_system_used']} systems, {values['within_system_skipped']} skipped)")
    if args.pairs:
        pairs = report["pairs"]
        print(f"pairs (gap {args.pair_gap}): {pairs['pairs']} on {pairs['sentences']} sentences, "
              f"system rule {100 * pairs['point']['system_rule']:.1f}, draws kept {pairs['draws_kept']}")
        for judge in judges:
            point = pairs["point"]
            print(f"  {judge:11s} {100 * point[judge]:.1f}  (rule right {100 * point[judge + '_rule_right']:.1f}, "
                  f"rule wrong {100 * point[judge + '_rule_wrong']:.1f})")


if __name__ == "__main__":
    main()
