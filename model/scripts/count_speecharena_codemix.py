#!/usr/bin/env python3
"""Count code-mixed pairs in SpeechArenaBench (one language, Hindi by default) without downloading audio.

Reads only the text and metadata columns of each parquet shard over HTTP.
Code-mixed = the sentence has at least one Latin letter AND at least one letter of the language's own script
(Devanagari for hi and mr, Kannada script for kn; see switchmos.data.load_speecharena.SCRIPTS).
Also counts the votes between two allowed (tier A+B) systems per pairing, with the decided (A or B) votes, which is
what Paper A uses.
Needs pyarrow, huggingface_hub and fsspec (pip install), and a Hugging Face token with the dataset gate accepted:
    PYTHONPATH=src python model/scripts/count_speecharena_codemix.py [--lang hi] [--out stats.json]
"""
import argparse
import json

import pyarrow.parquet
from huggingface_hub import HfFileSystem

from switchmos.data.load_speecharena import ALLOWED_SYSTEMS, SCRIPTS, classify

ROOT = "datasets/ai4bharat/SpeechArenaBench"
COLUMNS = ["academic_prompt_id", "sentence", "model_a", "model_b", "preference_model", "fine_grained_eval", "user_id"]


def has_native(text, lang):
    """True if the text has a letter of the language's own script."""
    first, last = SCRIPTS[lang]
    for ch in text:
        if first <= ch <= last:
            return True
    return False


def has_latin(text):
    """True if the text has an English letter A-Z or a-z."""
    for ch in text:
        if ch.isascii() and ch.isalpha():
            return True
    return False


def kind(sentence, lang):
    """'mixed', 'latin_only', 'native_only' or 'other', from the scripts used in the sentence."""
    native = has_native(sentence, lang)
    latin = has_latin(sentence)
    if native and latin:
        return "mixed"
    if latin:
        return "latin_only"
    if native:
        return "native_only"
    return "other"


def allowed_counts(rows, lang):
    """Votes between two allowed systems, per pairing: all, decided (A or B), decided mixed, and unknown values."""
    pairings = {}
    for row in rows:
        if row["model_a"] not in ALLOWED_SYSTEMS or row["model_b"] not in ALLOWED_SYSTEMS:
            continue
        pairing = " vs ".join(sorted([row["model_a"], row["model_b"]]))
        block = pairings.setdefault(pairing, {"votes": 0, "decided": 0, "decided_mixed": 0, "unrecognised": 0})
        block["votes"] += 1
        try:
            vote, tie_kind = classify(row["preference_model"], row["model_a"], row["model_b"])
        except ValueError:
            block["unrecognised"] += 1
            continue
        if vote in ["A", "B"]:
            block["decided"] += 1
            if kind(row["sentence"] or "", lang) == "mixed":
                block["decided_mixed"] += 1
    totals = {"votes": 0, "decided": 0, "decided_mixed": 0, "unrecognised": 0}
    for block in pairings.values():
        for key in totals:
            totals[key] += block[key]
    return {"totals": totals, "pairings": pairings}


def add_count(counts, key):
    """Add 1 to counts[key]."""
    counts[key] = counts.get(key, 0) + 1


def count_of(item):
    """Sort key for (key, count) pairs."""
    return item[1]


def top_counts(counts, n):
    """The n most common (key, count) pairs; equal counts keep their first-seen order."""
    return sorted(counts.items(), key=count_of, reverse=True)[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="hi")
    ap.add_argument("--out", default=None)
    ap.add_argument("--samples", type=int, default=15)
    args = ap.parse_args()

    fs = HfFileSystem()
    shards = sorted(fs.glob(f"{ROOT}/{args.lang}/*.parquet"))
    rows = []
    for i, shard in enumerate(shards):
        with fs.open(shard, "rb") as f:
            parquet_file = pyarrow.parquet.ParquetFile(f)
            columns = [c for c in COLUMNS if c in parquet_file.schema_arrow.names]
            # to_pylist keeps missing values as None (pandas would turn them into NaN)
            shard_rows = parquet_file.read(columns=columns).to_pylist()
        rows.extend(shard_rows)
        print(f"shard {i + 1}/{len(shards)}: {len(shard_rows)} rows (total {len(rows)})", flush=True)

    pairs_by_kind = {}
    sentences = {}    # prompt id -> sentence (first one seen)
    for row in rows:
        add_count(pairs_by_kind, kind(row["sentence"] or "", args.lang))
        if row["academic_prompt_id"] not in sentences:
            sentences[row["academic_prompt_id"]] = row["sentence"] or ""

    sentences_by_kind = {}
    for sentence in sentences.values():
        add_count(sentences_by_kind, kind(sentence, args.lang))

    systems = {}
    mixed_systems = {}
    preferences = {}
    raters = set()
    mixed_raters = set()
    for row in rows:
        is_mixed = kind(row["sentence"] or "", args.lang) == "mixed"
        for model in (row["model_a"], row["model_b"]):
            add_count(systems, model)
            if is_mixed:
                add_count(mixed_systems, model)
        add_count(preferences, str(row["preference_model"])[:40])
        raters.add(row["user_id"])
        if is_mixed:
            mixed_raters.add(row["user_id"])

    mixed_sentences = [s for s in sentences.values() if kind(s, args.lang) == "mixed"]
    latin_words = []
    for sentence in mixed_sentences:
        latin_words.append(len([w for w in sentence.split() if has_latin(w)]))
    if latin_words:
        latin_stats = {"mean": round(sum(latin_words) / len(latin_words), 2), "min": min(latin_words), "max": max(latin_words)}
    else:
        latin_stats = {"mean": 0.0, "min": 0, "max": 0}

    fine_grained_examples = None
    if "fine_grained_eval" in rows[0]:
        fine_grained_examples = [row["fine_grained_eval"] for row in rows[:3]]

    out = {
        "lang": args.lang,
        "shards": len(shards),
        "pairs_total": len(rows),
        "pairs_by_kind": pairs_by_kind,
        "unique_sentences": len(sentences),
        "sentences_by_kind": sentences_by_kind,
        "latin_words_per_mixed_sentence": latin_stats,
        "raters_total": len(raters),
        "raters_on_mixed": len(mixed_raters),
        "system_appearances": systems,
        "system_appearances_mixed": mixed_systems,
        "allowed_systems": allowed_counts(rows, args.lang),
        "preference_values_top": top_counts(preferences, 10),
        "fine_grained_eval_examples": fine_grained_examples,
        "mixed_sentence_samples": mixed_sentences[:args.samples],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    main()
