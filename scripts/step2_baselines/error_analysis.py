"""Step 2 error analysis: where and why do the four judges fail on Hindi and Hinglish? (read-only)

The checks (planned in the error-analysis document, approved 13 Oct):
  E1  accuracy per system pairing, for every judge (SpeechArenaBench, SAB)
  E2  which system each judge prefers in each pairing, against what people prefer; mean judge score per system
  E3  is code-mixing itself harder? Hinglish minus Hindi-only accuracy INSIDE each pairing, averaged over pairings,
      with a 95% interval (resampling sentences). Also SpeechJudge: Chinese-English minus the rest
  E4  accuracy for 0, 1, 2 and 3+ language switches in the sentence (inside each pairing, then averaged)
  E5  accuracy by the size of the score gap between the two clips (close calls vs clear wins)
  E6  accuracy by clip length and by the length ratio of the two clips (very short or very long takes)
  E7  do the four judges fail on the same votes?
  E8  MANGO Hindi: is the near-zero correlation real or noise? (95% interval, per-system means, without anchor/reference)
  E9  SpeechJudge: accuracy when people chose A vs B, and on the sentences not seen in training
  Listening list: the Hinglish votes where all four judges were most confidently wrong, with their clips copied out
  and a sheet for your tags.

Reads the exam tables (datasets/_exam/), the SAB sentences (datasets/_harmonized/speecharena_pairs.parquet), the score
files (analysis/step2/scores/) and the clip lengths (audio file headers only). Writes, atomically:
  <out>/error_analysis.json, <out>/error_analysis.md, <out>/listening_sheet.csv, <out>/listening/ (clips + README.txt)

Run (server, CPU only, a few minutes):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/error_analysis.py \
      --root ~/projects/hinglish-cs-tts/datasets --scores ~/projects/hinglish-cs-tts/analysis/step2/scores \
      --out ~/projects/hinglish-cs-tts/analysis/step2/error_analysis
"""
import argparse
import math
import random
import shutil
from pathlib import Path

import pandas as pd
import soundfile

from switchmos import files
from switchmos.eval import metrics

JUDGES = ["utmos", "utmosv2", "distillmos", "scoreq"]
BOOTSTRAP_ROUNDS = 1000
LISTENING_VOTES = 40
TAGS = ["switch point", "English word mispronounced", "name or number", "rhythm or intonation",
        "cut-off or extra speech", "noise", "can't tell"]


# ---------- small helpers ----------

def load_scores(scores_dir):
    """{judge: {audio path: score}} for every judge that has a score file."""
    scores = {}
    for judge in JUDGES:
        path = Path(scores_dir) / f"{judge}.csv"
        if path.exists():
            df = pd.read_csv(path)
            scores[judge] = dict(zip(df["path"], df["score"]))
    return scores


def credit(score_a, score_b, label):
    """1 if the higher score went to the clip people chose, 0.5 for equal scores, 0 otherwise
    (the same rule as metrics.pairwise_accuracy)."""
    if score_a == score_b:
        return 0.5
    a_scored_higher = score_a > score_b
    people_chose_a = label == "A"
    if a_scored_higher == people_chose_a:
        return 1.0
    return 0.0


def add_judge_columns(record, scores):
    """Add <judge>_a, <judge>_b and <judge>_credit to one pair record (None when a score is missing)."""
    for judge in scores:
        score_a = scores[judge].get(record["path_a"])
        score_b = scores[judge].get(record["path_b"])
        record[f"{judge}_a"] = score_a
        record[f"{judge}_b"] = score_b
        if score_a is None or score_b is None:
            record[f"{judge}_credit"] = None
        else:
            record[f"{judge}_credit"] = credit(score_a, score_b, record["label"])


def accuracy(records, judge):
    """(accuracy, number of scored records) of one judge on a list of records; accuracy is None if nothing is scored."""
    credits = []
    for record in records:
        if record[f"{judge}_credit"] is not None:
            credits.append(record[f"{judge}_credit"])
    if len(credits) == 0:
        return None, 0
    return sum(credits) / len(credits), len(credits)


def group_by(records, key):
    """{value of key: list of records with that value}, in order of first appearance."""
    groups = {}
    for record in records:
        value = record[key]
        if value not in groups:
            groups[value] = []
        groups[value].append(record)
    return groups


def average(values):
    """Mean of a list, or None for an empty list."""
    if len(values) == 0:
        return None
    return sum(values) / len(values)


def macro_accuracy(records, judge):
    """Accuracy inside each system pairing, then the average over the pairings (each pairing counts equally)."""
    per_pairing = []
    for pairing_records in group_by(records, "pairing").values():
        value, n = accuracy(pairing_records, judge)
        if value is not None:
            per_pairing.append(value)
    return average(per_pairing)


def bootstrap_interval(records, statistic, judge, rng):
    """95% interval of statistic(records, judge), resampling whole sentences (votes on one sentence are not independent)."""
    by_sentence = group_by(records, "sentence_id")
    sentences = list(by_sentence)
    values = []
    for round_number in range(BOOTSTRAP_ROUNDS):
        sample = []
        for sentence in rng.choices(sentences, k=len(sentences)):
            sample.extend(by_sentence[sentence])
        value = statistic(sample, judge)
        if value is not None:
            values.append(value)
    if len(values) == 0:
        return None, None
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def equal_bins(ordered, n_bins):
    """Cut an already sorted list into n_bins groups of (almost) equal size."""
    size = len(ordered) // n_bins
    bins = []
    for i in range(n_bins):
        start = i * size
        end = (i + 1) * size
        if i == n_bins - 1:
            end = len(ordered)          # the last bin takes the remainder
        bins.append(ordered[start:end])
    return bins


def get_gap(record):
    """Sort helper: the score gap of a record."""
    return record["gap"]


def get_mean_seconds(record):
    """Sort helper: the mean clip length of a record."""
    return record["mean_seconds"]


def get_confidence(record):
    """Sort helper: how confidently the judges were wrong on a record."""
    return record["confidence"]


def r4(value):
    """Round to 4 decimals, keeping None."""
    if value is None:
        return None
    return round(value, 4)


def three(value):
    """'0.123' for a correlation, '-' for None (for the markdown tables)."""
    if value is None:
        return "-"
    return f"{value:.3f}"


def percent(value):
    """'61.2' for 0.612, '-' for None (for the markdown tables)."""
    if value is None:
        return "-"
    return f"{100 * value:.1f}"


# ---------- language switches (the same rule as model/scripts/01_prepare_hiacc.py) ----------

def token_language(token):
    """'hi' for a word with a Devanagari letter, 'en' for a word with an English letter, 'other' for anything else."""
    for ch in token:
        if "ऀ" <= ch <= "ॿ":
            return "hi"
    for ch in token:
        if ch.isascii() and ch.isalpha():
            return "en"
    return "other"


def count_switches(sentence):
    """Number of times the language changes between neighbouring Hindi/English words."""
    languages = []
    for token in str(sentence).split():
        language = token_language(token)
        if language != "other":
            languages.append(language)
    switches = 0
    for i in range(1, len(languages)):
        if languages[i] != languages[i - 1]:
            switches += 1
    return switches


# ---------- reading the exams ----------

def read_sab_votes(root, scores):
    """The decided SAB votes (A or B, both clips present) as a list of records."""
    votes = pd.read_csv(root / "_exam" / "votes_speecharena.csv")
    pairs = pd.read_parquet(root / "_harmonized" / "speecharena_pairs.parquet", columns=["pair_id", "transcript"])
    sentence_of_pair = dict(zip(pairs["pair_id"], pairs["transcript"]))
    records = []
    for row in votes.to_dict("records"):
        if row["audio_status"] != "ok" or row["label"] not in ("A", "B"):
            continue
        sentence = sentence_of_pair[row["pair_id"]]
        record = {
            "vote_id": row["vote_id"],
            "pair_id": row["pair_id"],
            "sentence_id": str(row["sentence_id"]),
            "sentence": sentence,
            "n_switches": count_switches(sentence),
            "mixed": bool(row["mixed"]),
            "system_a": row["system_a"],
            "system_b": row["system_b"],
            "pairing": " vs ".join(sorted([row["system_a"], row["system_b"]])),
            "label": row["label"],
            "path_a": row["path_a"],
            "path_b": row["path_b"],
        }
        add_judge_columns(record, scores)
        records.append(record)
    return records


def read_speechjudge_pairs(root, scores):
    """The SpeechJudge test pairs with a clear winner as a list of records."""
    pairs = pd.read_csv(root / "_exam" / "pairs_speechjudge.csv")
    records = []
    for row in pairs.to_dict("records"):
        if row["label"] not in ("A", "B"):
            continue
        record = {
            "pair_id": row["pair_id"],
            "sentence_id": str(row["sentence_id"]),
            "mixed": row["lang"] == "zh-en",
            "sentence_in_train": bool(row["sentence_in_train"]),
            "label": row["label"],
            "path_a": row["path_a"],
            "path_b": row["path_b"],
        }
        add_judge_columns(record, scores)
        records.append(record)
    return records


# ---------- the checks ----------

def check_e1(votes, judges):
    """E1: accuracy per pairing and the average over pairings; checked against metrics.pairwise_accuracy."""
    result = {}
    for pairing, records in group_by(votes, "pairing").items():
        result[pairing] = {"n": len(records)}
        for judge in judges:
            value, n = accuracy(records, judge)
            # self-check: our credit rule must give exactly the evaluation's number
            scored = [r for r in records if r[f"{judge}_credit"] is not None]
            expected = metrics.pairwise_accuracy([r[f"{judge}_a"] for r in scored], [r[f"{judge}_b"] for r in scored],
                                                 [r["label"] for r in scored])
            assert abs(value - expected) < 1e-12, f"E1 mismatch for {judge} on {pairing}"
            result[pairing][judge] = r4(value)
    result["average over pairings"] = {}
    for judge in judges:
        result["average over pairings"][judge] = r4(macro_accuracy(votes, judge))
    return result


def check_e2(votes, judges):
    """E2: in each pairing, how often people and each judge pick the alphabetically first system; mean score per system."""
    per_pairing = {}
    for pairing, records in group_by(votes, "pairing").items():
        first_system = pairing.split(" vs ")[0]
        people = 0
        for record in records:
            if winner_system(record) == first_system:
                people += 1
        entry = {"system": first_system, "n": len(records), "people_pick_it": r4(people / len(records))}
        for judge in judges:
            picks = []
            for record in records:
                if record[f"{judge}_a"] is None or record[f"{judge}_b"] is None:
                    continue
                if record[f"{judge}_a"] == record[f"{judge}_b"]:
                    picks.append(0.5)
                elif judge_pick_system(record, judge) == first_system:
                    picks.append(1.0)
                else:
                    picks.append(0.0)
            entry[f"{judge}_picks_it"] = r4(average(picks))
        per_pairing[pairing] = entry

    mean_score = {}
    for judge in judges:
        scores_of_system = {}
        for record in votes:
            for side in ["a", "b"]:
                score = record[f"{judge}_{side}"]
                if score is None:
                    continue
                system = record[f"system_{side}"]
                if system not in scores_of_system:
                    scores_of_system[system] = []
                scores_of_system[system].append(score)
        mean_score[judge] = {}
        for system in sorted(scores_of_system):
            mean_score[judge][system] = r4(average(scores_of_system[system]))
    win_rate = {}
    for system in sorted(mean_score[judges[0]]):
        wins = 0
        appearances = 0
        for record in votes:
            if system in (record["system_a"], record["system_b"]):
                appearances += 1
                if winner_system(record) == system:
                    wins += 1
        win_rate[system] = r4(wins / appearances)
    return {"per_pairing": per_pairing, "mean_score_per_system": mean_score, "people_win_rate_per_system": win_rate}


def winner_system(record):
    """The system people chose in this vote."""
    if record["label"] == "A":
        return record["system_a"]
    return record["system_b"]


def judge_pick_system(record, judge):
    """The system whose clip got the higher score from this judge."""
    if record[f"{judge}_a"] > record[f"{judge}_b"]:
        return record["system_a"]
    return record["system_b"]


def mixed_minus_single(records, judge):
    """Inside each pairing: accuracy on Hinglish minus accuracy on Hindi-only; then the average over pairings."""
    differences = []
    for pairing_records in group_by(records, "pairing").values():
        mixed = [r for r in pairing_records if r["mixed"]]
        single = [r for r in pairing_records if not r["mixed"]]
        mixed_accuracy, n_mixed = accuracy(mixed, judge)
        single_accuracy, n_single = accuracy(single, judge)
        if mixed_accuracy is not None and single_accuracy is not None:
            differences.append(mixed_accuracy - single_accuracy)
    return average(differences)


def mixed_minus_rest(records, judge):
    """SpeechJudge: accuracy on Chinese-English pairs minus accuracy on the other pairs."""
    mixed_accuracy, n_mixed = accuracy([r for r in records if r["mixed"]], judge)
    rest_accuracy, n_rest = accuracy([r for r in records if not r["mixed"]], judge)
    if mixed_accuracy is None or rest_accuracy is None:
        return None
    return mixed_accuracy - rest_accuracy


def check_e3(votes, speechjudge, judges, rng):
    """E3: is code-mixing itself harder once the system pairing is fixed?"""
    result = {"sab": {}, "speechjudge": {}}
    for judge in judges:
        low, high = bootstrap_interval(votes, mixed_minus_single, judge, rng)
        result["sab"][judge] = {"mixed_minus_single": r4(mixed_minus_single(votes, judge)), "ci_low": r4(low), "ci_high": r4(high)}
        low, high = bootstrap_interval(speechjudge, mixed_minus_rest, judge, rng)
        result["speechjudge"][judge] = {"mixed_minus_rest": r4(mixed_minus_rest(speechjudge, judge)), "ci_low": r4(low), "ci_high": r4(high)}
    result["sab"]["n_mixed"] = len([r for r in votes if r["mixed"]])
    result["sab"]["n_single"] = len([r for r in votes if not r["mixed"]])
    return result


def switch_bin(n_switches):
    """'0', '1', '2' or '3+'."""
    if n_switches >= 3:
        return "3+"
    return str(n_switches)


def check_e4(votes, judges):
    """E4: accuracy (average over pairings) for 0, 1, 2 and 3+ switches; the stronger-system shortcut per bin for context."""
    result = {}
    for bin_name in ["0", "1", "2", "3+"]:
        records = [r for r in votes if switch_bin(r["n_switches"]) == bin_name]
        entry = {"n": len(records), "shortcut": r4(stronger_system_accuracy(records))}
        for judge in judges:
            entry[judge] = r4(macro_accuracy(records, judge))
        result[bin_name] = entry
    return result


def stronger_system_accuracy(records):
    """How often 'pick the system that wins more often in this pairing' is right (inside these records)."""
    if len(records) == 0:
        return None
    right = 0
    for pairing_records in group_by(records, "pairing").values():
        wins = {}
        for record in pairing_records:
            winner = winner_system(record)
            wins[winner] = wins.get(winner, 0) + 1
        right += max(wins.values())
    return right / len(records)


def check_e5(records, judges, n_bins=5):
    """E5: accuracy by the size of the score gap |score A - score B| (5 equal-sized groups, smallest gaps first)."""
    result = {}
    for judge in judges:
        scored = []
        for record in records:
            if record[f"{judge}_credit"] is not None:
                copy = dict(record)
                copy["gap"] = abs(record[f"{judge}_a"] - record[f"{judge}_b"])
                scored.append(copy)
        scored.sort(key=get_gap)
        bins = []
        for group in equal_bins(scored, n_bins):
            value, n = accuracy(group, judge)
            bins.append({"gap_from": r4(group[0]["gap"]), "gap_to": r4(group[-1]["gap"]), "n": n, "accuracy": r4(value)})
        result[judge] = bins
    return result


def ratio_bin(ratio):
    """Length ratio (longer / shorter clip) as a label."""
    if ratio < 1.25:
        return "under 1.25"
    if ratio < 1.5:
        return "1.25 to 1.5"
    if ratio < 2:
        return "1.5 to 2"
    if ratio < 3:
        return "2 to 3"
    return "3 or more"


def check_e6(votes, judges):
    """E6: accuracy by clip length and by the length ratio of the two clips; votes with a very short or very long clip."""
    seconds = {}
    for record in votes:
        for path in [record["path_a"], record["path_b"]]:
            if path not in seconds:
                info = soundfile.info(path)
                seconds[path] = info.frames / info.samplerate
    with_length = []
    for record in votes:
        copy = dict(record)
        length_a = seconds[record["path_a"]]
        length_b = seconds[record["path_b"]]
        copy["mean_seconds"] = (length_a + length_b) / 2
        copy["ratio"] = max(length_a, length_b) / max(min(length_a, length_b), 0.01)
        copy["extreme"] = min(length_a, length_b) < 1.0 or max(length_a, length_b) > 30.0
        with_length.append(copy)

    with_length.sort(key=get_mean_seconds)
    by_length = []
    for group in equal_bins(with_length, 5):
        entry = {"seconds_from": round(group[0]["mean_seconds"], 1), "seconds_to": round(group[-1]["mean_seconds"], 1), "n": len(group)}
        for judge in judges:
            entry[judge] = r4(accuracy(group, judge)[0])
        by_length.append(entry)

    by_ratio = {}
    for bin_name in ["under 1.25", "1.25 to 1.5", "1.5 to 2", "2 to 3", "3 or more"]:
        group = [r for r in with_length if ratio_bin(r["ratio"]) == bin_name]
        entry = {"n": len(group)}
        for judge in judges:
            entry[judge] = r4(accuracy(group, judge)[0])
        by_ratio[bin_name] = entry

    extreme = [r for r in with_length if r["extreme"]]
    extreme_entry = {"n": len(extreme)}
    for judge in judges:
        extreme_entry[judge] = r4(accuracy(extreme, judge)[0])
    return {"by_mean_length": by_length, "by_length_ratio": by_ratio, "a_clip_under_1s_or_over_30s": extreme_entry}


def check_e7(records, judges):
    """E7: on records scored by every judge, how many judges are wrong (credit 0) on the same record."""
    complete = []
    for record in records:
        all_scored = True
        for judge in judges:
            if record[f"{judge}_credit"] is None:
                all_scored = False
        if all_scored:
            complete.append(record)
    counts = {}
    for n_wrong in range(len(judges) + 1):
        counts[str(n_wrong)] = 0
    for record in complete:
        n_wrong = 0
        for judge in judges:
            if record[f"{judge}_credit"] == 0.0:
                n_wrong += 1
        counts[str(n_wrong)] += 1
    return {"n": len(complete), "number_of_judges_wrong": counts}


def check_e8(root, scores, judges, rng):
    """E8: MANGO Hindi test, per variant: SRCC with a 95% interval (resampling sentences), and without anchor/reference."""
    clips = pd.read_csv(root / "_exam" / "clips_mango.csv").fillna({"variant": ""})
    hindi = clips[(clips["lang"] == "hi") & (clips["split"] == "test") & (clips["audio_status"] == "ok")]
    result = {}
    for variant, group in hindi.groupby("variant"):
        records = []
        for row in group.to_dict("records"):
            record = {"sentence_id": Path(row["audio_path"]).name, "system": row["system"], "mos": row["mos"]}
            for judge in judges:
                record[judge] = scores[judge].get(row["path"])
            records.append(record)
        entry = {"n": len(records)}
        for judge in judges:
            low, high = bootstrap_interval(records, mango_srcc, judge, rng)
            without = [r for r in records if r["system"] not in ("anchor", "reference")]
            entry[judge] = {
                "srcc": r4(mango_srcc(records, judge)),
                "ci_low": r4(low),
                "ci_high": r4(high),
                "srcc_without_anchor_reference": r4(mango_srcc(without, judge)),
            }
        entry["system_means"] = mango_system_means(records, judges)
        result[variant] = entry
    return result


def mango_srcc(records, judge):
    """SRCC between the judge's score and the MUSHRA mean over the records (None if it cannot be computed)."""
    predictions = []
    humans = []
    for record in records:
        if record[judge] is not None:
            predictions.append(record[judge])
            humans.append(record["mos"])
    if len(predictions) < 3:
        return None
    value = metrics.spearman(predictions, humans)
    if math.isnan(value):
        return None
    return value


def mango_system_means(records, judges):
    """Mean MUSHRA score and mean judge score per system."""
    by_system = group_by(records, "system")
    means = {}
    for system in sorted(by_system):
        system_records = by_system[system]
        entry = {"n": len(system_records), "mushra": r4(average([r["mos"] for r in system_records]))}
        for judge in judges:
            values = [r[judge] for r in system_records if r[judge] is not None]
            entry[judge] = r4(average(values))
        means[system] = entry
    return means


def check_e9(speechjudge, judges):
    """E9: SpeechJudge accuracy when people chose A, when they chose B, and on sentences not seen in training."""
    result = {}
    subsets = {
        "people chose A": [r for r in speechjudge if r["label"] == "A"],
        "people chose B": [r for r in speechjudge if r["label"] == "B"],
        "sentence not in train": [r for r in speechjudge if not r["sentence_in_train"]],
    }
    for name, records in subsets.items():
        entry = {"n": len(records)}
        for judge in judges:
            entry[judge] = r4(accuracy(records, judge)[0])
        result[name] = entry
    result["protocol_note"] = ("SpeechJudge paper: same 1,000 test pairs (400 regular, 600 expressive), ties removed, "
                               "full-agreement pairs only, the higher MOS wins; UTMOS 53.7% there vs ours in E1/evaluation.")
    return result


def listening_list(votes, judges, out):
    """The Hinglish votes where all judges were wrong, ranked by how confidently; copies their clips and writes a sheet."""
    spread = {}
    for judge in judges:
        all_scores = []
        for record in votes:
            all_scores.append(record[f"{judge}_a"])
            all_scores.append(record[f"{judge}_b"])
        mean_score = average(all_scores)
        variance = average([(s - mean_score) ** 2 for s in all_scores])
        spread[judge] = math.sqrt(variance)

    candidates = []
    for record in votes:
        if not record["mixed"]:
            continue
        all_wrong = True
        for judge in judges:
            if record[f"{judge}_credit"] != 0.0:
                all_wrong = False
        if not all_wrong:
            continue
        # confidence: how far apart the two scores were (in units of that judge's spread), averaged over judges
        gaps = []
        for judge in judges:
            gaps.append(abs(record[f"{judge}_a"] - record[f"{judge}_b"]) / spread[judge])
        copy = dict(record)
        copy["confidence"] = average(gaps)
        candidates.append(copy)
    candidates.sort(key=get_confidence, reverse=True)      # most confident first
    chosen = candidates[:LISTENING_VOTES]

    folder = out / "listening"
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for rank in range(len(chosen)):
        record = chosen[rank]
        name = f"{rank + 1:02d}_{record['vote_id'].replace(':', '_')}"
        file_a = f"{name}_A.wav"
        file_b = f"{name}_B.wav"
        shutil.copyfile(record["path_a"], folder / file_a)
        shutil.copyfile(record["path_b"], folder / file_b)
        rows.append({
            "rank": rank + 1,
            "vote_id": record["vote_id"],
            "sentence": record["sentence"],
            "n_switches": record["n_switches"],
            "clip_A_file": file_a,
            "clip_A_system": record["system_a"],
            "clip_B_file": file_b,
            "clip_B_system": record["system_b"],
            "people_chose": record["label"],
            "judges_chose": "the other clip (all four)",
            "confidence": round(record["confidence"], 3),
            "cause": "",
            "notes": "",
        })
    files.save_csv(pd.DataFrame(rows), out / "listening_sheet.csv")
    readme = ("Listening notes (one listener, qualitative; never used as training or test labels).\n"
              "Each vote has two clips: <rank>_<vote>_A.wav and <rank>_<vote>_B.wav. People preferred the clip in the\n"
              "'people_chose' column; all four judges gave the higher score to the other clip.\n"
              "Listen to both, then write ONE cause in the 'cause' column of listening_sheet.csv:\n  "
              + "\n  ".join(TAGS) + "\n")
    files.save_text(folder / "README.txt", readme)
    return {"n_all_wrong_hinglish": len(candidates), "n_listed": len(chosen)}


# ---------- report ----------

def markdown_report(results, judges):
    """The main tables as markdown lines."""
    header = "| | " + " | ".join(judges) + " |"
    rule = "|---|" + "---|" * len(judges)
    lines = ["# Step 2 error analysis", "", "Accuracy in percent. SAB = SpeechArenaBench decided votes.", ""]

    lines += ["## E1 Accuracy per system pairing (SAB)", "", header.replace("| |", "| Pairing (n) |"), rule]
    for pairing, entry in results["E1"].items():
        cells = [percent(entry[judge]) for judge in judges]
        if "n" in entry:
            lines.append(f"| {pairing} ({entry['n']}) | " + " | ".join(cells) + " |")
        else:
            lines.append(f"| **{pairing}** | " + " | ".join(cells) + " |")

    lines += ["", "## E2 Mean judge score per system, and how often people pick each system (SAB)", "",
              "| System | people win rate | " + " | ".join(judges) + " |", "|---|---|" + "---|" * len(judges)]
    for system, rate in results["E2"]["people_win_rate_per_system"].items():
        cells = [str(results["E2"]["mean_score_per_system"][judge][system]) for judge in judges]
        lines.append(f"| {system} | {percent(rate)} | " + " | ".join(cells) + " |")

    lines += ["", "## E3 Hinglish minus Hindi-only accuracy inside each pairing (points, 95% interval)", "",
              "| Exam | " + " | ".join(judges) + " |", rule]
    for exam, key in [("sab", "mixed_minus_single"), ("speechjudge", "mixed_minus_rest")]:
        cells = []
        for judge in judges:
            entry = results["E3"][exam][judge]
            cells.append(f"{percent(entry[key])} [{percent(entry['ci_low'])}, {percent(entry['ci_high'])}]")
        lines.append(f"| {exam} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("An interval that includes 0 means no clear difference.")

    lines += ["", "## E4 Accuracy by number of language switches (average over pairings, SAB)", "",
              "| Switches (n) | shortcut | " + " | ".join(judges) + " |", "|---|---|" + "---|" * len(judges)]
    for bin_name, entry in results["E4"].items():
        cells = [percent(entry[judge]) for judge in judges]
        lines.append(f"| {bin_name} ({entry['n']}) | {percent(entry['shortcut'])} | " + " | ".join(cells) + " |")

    for exam in ["sab", "speechjudge"]:
        lines += ["", f"## E5 Accuracy by score gap, smallest gaps first ({exam})", "",
                  "| Judge | " + " | ".join(["bin 1", "bin 2", "bin 3", "bin 4", "bin 5"]) + " |", "|---|" + "---|" * 5]
        for judge in judges:
            cells = [percent(b["accuracy"]) for b in results["E5"][exam][judge]]
            lines.append(f"| {judge} | " + " | ".join(cells) + " |")

    lines += ["", "## E6 Accuracy by length ratio of the two clips (SAB)", "", "| Ratio (n) | " + " | ".join(judges) + " |", rule]
    for bin_name, entry in results["E6"]["by_length_ratio"].items():
        cells = [percent(entry[judge]) for judge in judges]
        lines.append(f"| {bin_name} ({entry['n']}) | " + " | ".join(cells) + " |")
    extreme = results["E6"]["a_clip_under_1s_or_over_30s"]
    cells = [percent(extreme[judge]) for judge in judges]
    lines.append(f"| a clip under 1 s or over 30 s ({extreme['n']}) | " + " | ".join(cells) + " |")

    lines += ["", "## E7 How many judges are wrong on the same vote", ""]
    for exam in ["sab", "speechjudge"]:
        counts = results["E7"][exam]["number_of_judges_wrong"]
        parts = [f"{k} wrong: {v}" for k, v in counts.items()]
        lines.append(f"- {exam} (n {results['E7'][exam]['n']}): " + ", ".join(parts))

    lines += ["", "## E8 MANGO Hindi test: SRCC [95% interval] / without anchor and reference", "",
              "| Variant (n) | " + " | ".join(judges) + " |", rule]
    for variant, entry in results["E8"].items():
        cells = []
        for judge in judges:
            j = entry[judge]
            cells.append(f"{three(j['srcc'])} [{three(j['ci_low'])}, {three(j['ci_high'])}] / {three(j['srcc_without_anchor_reference'])}")
        lines.append(f"| {variant} ({entry['n']}) | " + " | ".join(cells) + " |")

    lines += ["", "## E9 SpeechJudge", "", "| Subset (n) | " + " | ".join(judges) + " |", rule]
    for name, entry in results["E9"].items():
        if name == "protocol_note":
            continue
        cells = [percent(entry[judge]) for judge in judges]
        lines.append(f"| {name} ({entry['n']}) | " + " | ".join(cells) + " |")
    lines += ["", results["E9"]["protocol_note"]]

    listening = results["listening"]
    lines += ["", "## Listening list", "",
              f"{listening['n_all_wrong_hinglish']} Hinglish votes where all four judges were wrong; the "
              f"{listening['n_listed']} most confident ones are in listening/ and listening_sheet.csv."]
    return lines


def main():
    parser = argparse.ArgumentParser(description="Step 2 error analysis (E1-E9 and the listening list).")
    parser.add_argument("--root", required=True, help="the datasets folder")
    parser.add_argument("--scores", required=True, help="the folder with <judge>.csv score files")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.root).expanduser()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    scores = load_scores(args.scores)
    judges = []
    for judge in JUDGES:
        if judge in scores:
            judges.append(judge)
    rng = random.Random(0)          # fixed seed: the same intervals every run

    votes = read_sab_votes(root, scores)
    speechjudge = read_speechjudge_pairs(root, scores)
    print(f"{len(votes)} decided SAB votes, {len(speechjudge)} SpeechJudge pairs, judges {judges}", flush=True)

    results = {"judges": judges, "n_sab_votes": len(votes), "n_speechjudge_pairs": len(speechjudge)}
    results["E1"] = check_e1(votes, judges)
    results["E2"] = check_e2(votes, judges)
    results["E3"] = check_e3(votes, speechjudge, judges, rng)
    results["E4"] = check_e4(votes, judges)
    results["E5"] = {"sab": check_e5(votes, judges), "speechjudge": check_e5(speechjudge, judges)}
    print("E1-E5 done; reading clip lengths for E6", flush=True)
    results["E6"] = check_e6(votes, judges)
    results["E7"] = {"sab": check_e7(votes, judges), "speechjudge": check_e7(speechjudge, judges)}
    results["E8"] = check_e8(root, scores, judges, rng)
    results["E9"] = check_e9(speechjudge, judges)
    results["listening"] = listening_list(votes, judges, out)

    files.save_json(out / "error_analysis.json", results)
    files.save_text(out / "error_analysis.md", "\n".join(markdown_report(results, judges)) + "\n")
    print(f"written: {out / 'error_analysis.md'}", flush=True)


if __name__ == "__main__":
    main()
