#!/usr/bin/env python3
"""Count code-mixed pairs in SpeechArenaBench (one language, Hindi by default) without downloading audio.

Reads only the text and metadata columns of each parquet shard over HTTP.
Code-mixed = the sentence has at least one Latin-script word AND at least one Devanagari word.
Needs pyarrow, huggingface_hub and fsspec (pip install), and a Hugging Face token with the dataset gate accepted:
    python model/scripts/count_speecharena_codemix.py [--lang hi] [--out stats.json]
"""
import argparse
import json

import pyarrow.parquet
from huggingface_hub import HfFileSystem

ROOT = "datasets/ai4bharat/SpeechArenaBench"
COLUMNS = ["academic_prompt_id", "sentence", "model_a", "model_b", "preference_model", "fine_grained_eval", "user_id"]


def has_devanagari(text):
    """True if the text has a Devanagari character (U+0900 to U+097F)."""
    for ch in text:
        if "ऀ" <= ch <= "ॿ":
            return True
    return False


def has_latin(text):
    """True if the text has an English letter A-Z or a-z."""
    for ch in text:
        if ch.isascii() and ch.isalpha():
            return True
    return False


def kind(sentence):
    """'mixed', 'latin_only', 'dev_only' or 'other', from the scripts used in the sentence."""
    dev = has_devanagari(sentence)
    latin = has_latin(sentence)
    if dev and latin:
        return "mixed"
    if latin:
        return "latin_only"
    if dev:
        return "dev_only"
    return "other"


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
        add_count(pairs_by_kind, kind(row["sentence"] or ""))
        if row["academic_prompt_id"] not in sentences:
            sentences[row["academic_prompt_id"]] = row["sentence"] or ""

    sentences_by_kind = {}
    for sentence in sentences.values():
        add_count(sentences_by_kind, kind(sentence))

    systems = {}
    mixed_systems = {}
    preferences = {}
    raters = set()
    mixed_raters = set()
    for row in rows:
        is_mixed = kind(row["sentence"] or "") == "mixed"
        for model in (row["model_a"], row["model_b"]):
            add_count(systems, model)
            if is_mixed:
                add_count(mixed_systems, model)
        add_count(preferences, str(row["preference_model"])[:40])
        raters.add(row["user_id"])
        if is_mixed:
            mixed_raters.add(row["user_id"])

    mixed_sentences = [s for s in sentences.values() if kind(s) == "mixed"]
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
