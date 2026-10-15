"""First failure-analysis pass from saved predictions; no training or scoring.

Checks saved results, compares paired judge errors, corrects shortcut weighting,
and prepares matched listening controls. All new comparisons are exploratory.
Uses numpy and the existing metric functions; writes only --out.
"""
import argparse
import csv
import itertools
import json
import math
import datetime
import subprocess
import sys
from pathlib import Path

from switchmos import files

JUDGES = ["utmos", "utmosv2", "distillmos", "scoreq"]


def read_csv(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def save_rows(path, rows):
    if not rows:
        return
    temporary = Path(str(path) + ".tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def group_by(rows, key):
    groups = {}
    for row in rows:
        groups.setdefault(row[key], []).append(row)
    return groups


def mean(values):
    return sum(values) / len(values) if len(values) else None


def credit(score_a, score_b, label):
    if score_a == score_b:
        return 0.5
    return float((score_a > score_b) == (label == "A"))


def join_scores(rows, scores, sab):
    records = []
    for source in rows:
        if source["label"] not in ["A", "B"] or source.get("audio_status", "ok") != "ok":
            continue
        row = dict(source)
        row["id"] = row["vote_id"] if sab else row["pair_id"]
        row["mixed"] = row["mixed"] == "True"
        row["pairing"] = " vs ".join(sorted([row["system_a"], row["system_b"]])) if sab else "all"
        row["winner"] = row["system_a"] if row["label"] == "A" else row["system_b"]
        if not sab:
            row["winner"] = row["label"]
        for judge in JUDGES:
            a = scores[judge][row["path_a"]]
            b = scores[judge][row["path_b"]]
            row[judge + "_a"] = a
            row[judge + "_b"] = b
            row[judge + "_credit"] = credit(a, b, row["label"])
        row["all_wrong"] = all([row[judge + "_credit"] == 0 for judge in JUDGES])
        row["all_right"] = all([row[judge + "_credit"] == 1 for judge in JUDGES])
        records.append(row)
    return records


def summary(rows):
    groups = group_by(rows, "pairing")
    per_pairing = {}
    for name, group in groups.items():
        winners = group_by(group, "winner")
        block = {"n":len(group), "winner_counts":{key:len(value) for key,value in winners.items()},
                 "oracle":max([len(value) for value in winners.values()]) / len(group)}
        for judge in JUDGES:
            block[judge] = mean([row[judge + "_credit"] for row in group])
            block[judge + "_winner_balanced"] = None
            if len(winners) == 2:
                block[judge + "_winner_balanced"] = mean([
                    mean([row[judge + "_credit"] for row in subset]) for subset in winners.values()])
        per_pairing[name] = block
    result = {"n":len(rows), "sentences":len(group_by(rows, "sentence_id")), "per_pairing":per_pairing,
              "all_wrong":sum([row["all_wrong"] for row in rows]),
              "all_right":sum([row["all_right"] for row in rows]),
              "always_A":mean([float(row["label"] == "A") for row in rows]),
              "oracle_micro":sum([value["oracle"] * value["n"] for value in per_pairing.values()]) / len(rows),
              "oracle_macro":mean([value["oracle"] for value in per_pairing.values()])}
    for judge in JUDGES:
        result[judge] = {"micro":mean([row[judge + "_credit"] for row in rows]),
                         "macro":mean([value[judge] for value in per_pairing.values()]),
                         "model_ties":sum([row[judge + "_credit"] == 0.5 for row in rows]),
                         "winner_balanced_macro":mean([value[judge + "_winner_balanced"]
                             for value in per_pairing.values() if value[judge + "_winner_balanced"] is not None])}
    return result


def paired_comparisons(rows, rounds, seed):
    """Paired sentence-cluster bootstrap; same draw for all judges and pairings."""
    import numpy as np

    sentences = sorted(group_by(rows, "sentence_id"))
    pairings = sorted(group_by(rows, "pairing"))
    sentence_index = {key:index for index,key in enumerate(sentences)}
    pairing_index = {key:index for index,key in enumerate(pairings)}
    counts = np.zeros((len(sentences), len(pairings)))
    credits = np.zeros((len(sentences), len(pairings), len(JUDGES)))
    for row in rows:
        s = sentence_index[row["sentence_id"]]
        p = pairing_index[row["pairing"]]
        counts[s,p] += 1
        for j, judge in enumerate(JUDGES):
            credits[s,p,j] += row[judge + "_credit"]
    rng = np.random.default_rng(seed)
    boot_micro = []
    boot_macro = []
    for iteration in range(rounds):
        draw = rng.integers(0, len(sentences), size=len(sentences))
        n = counts[draw].sum(axis=0)
        total = credits[draw].sum(axis=0)
        boot_micro.append(total.sum(axis=0) / n.sum())
        if np.all(n > 0):
            boot_macro.append((total / n[:,None]).mean(axis=0))
    boot_micro = np.array(boot_micro)
    boot_macro = np.array(boot_macro)
    point = summary(rows)
    comparisons = []
    for old, new in itertools.combinations(JUDGES, 2):
        old_index = JUDGES.index(old)
        new_index = JUDGES.index(new)
        result = {"old":old, "new":new, "n":len(rows), "sentences":len(sentences),
                  "fixed_strict_errors":sum([row[old + "_credit"] == 0 and row[new + "_credit"] == 1 for row in rows]),
                  "introduced_strict_errors":sum([row[old + "_credit"] == 1 and row[new + "_credit"] == 0 for row in rows]),
                  "fractional_credit_gain":sum([row[new + "_credit"] - row[old + "_credit"] for row in rows])}
        for label, bootstrap in [("micro", boot_micro), ("macro", boot_macro)]:
            diff = bootstrap[:,new_index] - bootstrap[:,old_index]
            result[label + "_difference"] = point[new][label] - point[old][label]
            result[label + "_ci95"] = np.quantile(diff, [0.025, 0.975]).tolist()
            result[label + "_bootstrap_valid_draws"] = len(diff)
        comparisons.append(result)
    return comparisons


def check_close(actual, expected, label):
    if round(actual, 4) != expected:
        raise ValueError(f"Saved-result mismatch {label}: {actual} != {expected}")


def audit_saved(sab, speechjudge, final):
    subsets = {"decided_votes":sab, "decided_votes_mixed":[row for row in sab if row["mixed"]]}
    checked = 0
    for name, rows in subsets.items():
        assert len(rows) == final["speecharena"][name]["n"]
        for judge in JUDGES:
            check_close(mean([row[judge + "_credit"] for row in rows]), final["speecharena"][name][judge], name + judge)
            checked += 1
    for name, rows in group_by(sab, "pairing").items():
        assert len(rows) == final["speecharena"]["per_pairing"][name]["n"]
        for judge in JUDGES:
            check_close(mean([row[judge + "_credit"] for row in rows]), final["speecharena"]["per_pairing"][name][judge], name + judge)
            checked += 1
    subsets = {"all":speechjudge, "mixed_zh_en":[row for row in speechjudge if row["mixed"]],
               "sentence_disjoint":[row for row in speechjudge if row["sentence_in_train"] == "False"]}
    for name, rows in subsets.items():
        assert len(rows) == final["speechjudge"][name]["n"]
        for judge in JUDGES:
            check_close(mean([row[judge + "_credit"] for row in rows]), final["speechjudge"][name][judge], name + judge)
            checked += 1
    return checked


def count_switches(sentence):
    languages = []
    for token in sentence.split():
        language = None
        for char in token:
            if "ऀ" <= char <= "ॿ":
                language = "hi"
                break
        if language is None:
            for char in token:
                if char.isascii() and char.isalpha():
                    language = "en"
                    break
        if language is not None:
            languages.append(language)
    count = 0
    for index in range(1, len(languages)):
        count += languages[index] != languages[index - 1]
    return count


def select_controls(failures, sab):
    used = set()
    result = []
    for failure in failures:
        best = None
        best_key = None
        for candidate in sab:
            if not candidate["all_right"] or candidate["id"] in used:
                continue
            if candidate["pairing"] != failure["pairing"] or candidate["mixed"] != failure["mixed"]:
                continue
            distance = abs(math.log(candidate["mean_seconds"] / failure["mean_seconds"]))
            key = (candidate["sentence_id"] != failure["sentence_id"],
                   candidate["winner"] != failure["winner"], distance, candidate["id"])
            if best_key is None or key < best_key:
                best, best_key = candidate, key
        entry = {"failure_id":failure["id"], "control_id":"", "pairing":failure["pairing"],
                 "same_sentence":False, "same_human_winner":False, "duration_log_distance":""}
        if best is not None:
            used.add(best["id"])
            entry.update({"control_id":best["id"], "same_sentence":best["sentence_id"] == failure["sentence_id"],
                          "same_human_winner":best["winner"] == failure["winner"],
                          "duration_log_distance":best_key[2]})
        result.append(entry)
    return result


def main():
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--final-results", type=Path, required=True)
    parser.add_argument("--listening-sheet", type=Path, required=True)
    parser.add_argument("--listening-audio", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=2000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    scores = {}
    audio_list = read_csv(args.inputs / "exam/audio_list.csv")
    expected_paths = {row["path"] for row in audio_list}
    assert len(expected_paths) == len(audio_list) == 15445
    for judge in JUDGES:
        rows = read_csv(args.inputs / "scores" / (judge + ".csv"))
        lookup = {}
        for row in rows:
            assert row["path"] not in lookup, "Duplicate score path"
            lookup[row["path"]] = float(row["score"])
            assert math.isfinite(lookup[row["path"]]), "Non-finite score"
        assert set(lookup) == expected_paths, "Missing/extra score paths for " + judge
        scores[judge] = lookup
    sab_raw = read_csv(args.inputs / "exam/votes_speecharena.csv")
    assert len({row["vote_id"] for row in sab_raw}) == len(sab_raw) == 4444
    sab = join_scores(sab_raw, scores, True)
    sj = join_scores(read_csv(args.inputs / "exam/pairs_speechjudge.csv"), scores, False)
    final = files.load_json(args.final_results)
    checked = audit_saved(sab, sj, final)
    features = {row["path"]:row for row in read_csv(args.evidence / "audio_features.csv")}
    assert len(features) == 8804, "Incomplete audio feature coverage"
    assert not files.load_json(args.evidence / "audio_errors.json")
    assert not files.load_json(args.evidence / "identity_audit.json")["errors"]
    sentences = {row["pair_id"]:row["transcript"] for row in read_csv(args.evidence / "sentences.csv")}
    for row in sab:
        row["sentence"] = sentences[row["pair_id"]]
        row["n_switches"] = count_switches(row["sentence"])
        row["switch_bin"] = str(min(row["n_switches"], 3))
        row["has_digits"] = any([char.isdigit() for char in row["sentence"]])
        row["mean_seconds"] = mean([float(features[row["path_a"]]["seconds"]), float(features[row["path_b"]]["seconds"])])
        for field in ["seconds", "rms", "quiet_relative_fraction", "quiet_absolute_fraction", "near_full_scale_fraction"]:
            for side in ["a", "b"]:
                row[field + "_" + side] = float(features[row["path_" + side]][field])
    listening = read_csv(args.listening_sheet)
    by_id = {row["id"]:row for row in sab}
    failures = []
    listening_checks = []
    for selected in listening:
        row = by_id[selected["vote_id"]]
        assert row["all_wrong"] and row["mixed"]
        assert row["sentence"] == selected["sentence"] and row["label"] == selected["people_chose"]
        failures.append(row)
        for side in ["A", "B"]:
            path = args.listening_audio / selected["clip_" + side + "_file"]
            actual_hash = files.file_hash(path)
            assert actual_hash == features[row["path_" + side.lower()]]["sha256"], "Listening copy mismatch"
            listening_checks.append({"vote_id":row["id"], "side":side, "file":str(path), "sha256":actual_hash})
    subsets = {"sab_all":sab, "sab_mixed":[r for r in sab if r["mixed"]],
               "sab_single":[r for r in sab if not r["mixed"]], "speechjudge_all":sj,
               "speechjudge_mixed":[r for r in sj if r["mixed"]],
               "speechjudge_sentence_disjoint":[r for r in sj if r["sentence_in_train"] == "False"]}
    report = {"subsets":{}, "switch_bins":{}, "exploratory":True,
              "intervals":"Paired sentence-cluster percentile bootstrap; 2000 draws by default, seed 15. No multiplicity correction; not model selection."}
    for name, rows in subsets.items():
        print("Analysing", name, len(rows), flush=True)
        report["subsets"][name] = {"summary":summary(rows), "comparisons":paired_comparisons(rows,args.rounds,15)}
    for name, rows in group_by(sab, "switch_bin").items():
        report["switch_bins"][name] = summary(rows)
    groups = {"all_wrong":[r for r in sab if r["all_wrong"]],
              "all_right":[r for r in sab if r["all_right"]], "selected_40":failures}
    report["audio_descriptions"] = {}
    for name, rows in groups.items():
        block = {"n":len(rows), "sentences":len(group_by(rows,"sentence_id")),
                 "with_digits":sum([r["has_digits"] for r in rows])}
        for field in ["seconds", "rms", "quiet_relative_fraction", "quiet_absolute_fraction", "near_full_scale_fraction"]:
            diffs = []
            for row in rows:
                winner = "a" if row["label"] == "A" else "b"
                loser = "b" if winner == "a" else "a"
                diffs.append(row[field + "_" + winner] - row[field + "_" + loser])
            block[field + "_human_winner_minus_loser_median"] = float(np.median(diffs))
        report["audio_descriptions"][name] = block
    controls = select_controls(failures,sab)
    report["listening_controls"] = {"selected":len(controls),
        "matched":sum([bool(row["control_id"]) for row in controls]),
        "same_sentence":sum([row["same_sentence"] for row in controls]),
        "same_human_winner":sum([row["same_human_winner"] for row in controls]),
        "rule":"Unused all-four-correct case, same pairing and mixed flag; prefer same sentence, then same human winner, then closest log mean duration; ID tie-break. Convenience controls, not causal matching."}
    save_rows(args.out / "sab_cases.csv", sab)
    save_rows(args.out / "speechjudge_cases.csv", sj)
    save_rows(args.out / "matched_controls.csv", controls)
    save_rows(args.out / "listening_copy_checks.csv", listening_checks)
    files.save_json(args.out / "analysis.json", report)
    inputs = []
    for directory in [args.inputs, args.evidence]:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                inputs.append({"path":str(path), "sha256":files.file_hash(path)})
    for path in [args.final_results, args.listening_sheet]:
        inputs.append({"path":str(path), "sha256":files.file_hash(path)})
    files.save_json(args.out / "run_manifest.json", {
        "inputs":inputs, "script_sha256":files.file_hash(__file__), "numpy":np.__version__,
        "completed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python":sys.version, "command":sys.argv,
        "base_commit":subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "code_note":"New analysis script may be uncommitted at execution; the SHA-256 identifies the executed version.",
        "rounds":args.rounds, "seed":15, "saved_pair_accuracy_fields_reproduced":checked,
        "scores_per_judge":len(expected_paths), "listening_copies_checked":len(listening_checks),
        "note":"No training, model inference, audio edits or listening judgements. Descriptive analysis of an inspected test set."})
    print("DONE; saved accuracy fields reproduced:", checked, flush=True)


if __name__ == "__main__":
    main()
