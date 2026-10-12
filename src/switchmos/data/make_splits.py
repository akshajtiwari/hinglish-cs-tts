"""Freeze the train / val / test splits.

    PYTHONPATH=src python -m switchmos.data.make_splits --root ~/projects/hinglish-cs-tts/datasets [--versions tamil_out,tamil_in] [--force]

Reads <root>/_harmonized and writes <root>/_splits/<version>/<table>.parquet (id, split) plus manifest.json.
"""
import argparse
import hashlib
import time
from pathlib import Path
from pathlib import PurePosixPath

from switchmos.files import file_hash
from switchmos.files import save_json

RULES = """Split names: train, val, test, plus test_extra (an extra exam) and unused (kept out of v1).
Two versions:
  tamil_out: no Tamil in training. Tamil sentences in the common test bucket -> test; all other Tamil -> test_extra.
  tamil_in : Tamil is split by sentence like Hindi (train / val / test).
The Tamil test sentences are the SAME in both versions, so the two models are compared on one exam.

Rules per dataset:
  speechjudge : official train -> train, dev -> val, test -> test, other -> unused
  speecharena : everything -> test (test-only because of vendor terms)
  somos       : official train -> train, valid -> val, test -> test
  bvcc        : official train -> train, dev -> val, test -> test
  mango       : by sentence (the stimulus file name), exactly 80 / 10 / 10 within each language (hash-ordered),
                identical across variants and systems
Votes get the split of their pair.
Buckets come from a hash of the sentence key, not from random draws: the same result every time, whatever the row order.
"""

VERSIONS = ["tamil_out", "tamil_in"]
SPLIT_NAMES = ["train", "val", "test", "test_extra", "unused"]
OFFICIAL = {
    "speechjudge": {"train": "train", "dev": "val", "test": "test", "other": "unused"},
    "somos": {"train": "train", "valid": "val", "test": "test"},
    "bvcc": {"train": "train", "dev": "val", "test": "test"},
}
VAL_FRAC = 0.10
TEST_FRAC = 0.10
# table name: (dataset, id column, kind)
TABLES = {
    "speechjudge_pairs": ("speechjudge", "pair_id", "pairs"),
    "speechjudge_votes": ("speechjudge", "vote_id", "votes"),
    "speecharena_pairs": ("speecharena", "pair_id", "pairs"),
    "speecharena_votes": ("speecharena", "vote_id", "votes"),
    "mango_ratings": ("mango", "rating_id", "ratings"),
    "somos_ratings": ("somos", "rating_id", "ratings"),
    "bvcc_ratings": ("bvcc", "rating_id", "ratings"),
}


def sha1_text(text):
    """The sha1 hex digest of a text."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def rank_buckets(keys, val_frac=VAL_FRAC, test_frac=TEST_FRAC):
    """Give each distinct key a bucket with exact proportions and no random seed.

    The keys are sorted by their hash; the first test_frac go to test, the next val_frac to val, the rest to train.
    """
    ordered = sorted(set(keys), key=sha1_text)
    n_test = round(len(ordered) * test_frac)
    n_val = round(len(ordered) * val_frac)
    buckets = {}
    for i, key in enumerate(ordered):
        if i < n_test:
            buckets[key] = "test"
        elif i < n_test + n_val:
            buckets[key] = "val"
        else:
            buckets[key] = "train"
    return buckets


def mango_stimulus(audio_path, lang):
    """Sentence key: language + the stimulus file name (every system and variant uses the same file name)."""
    return f"{lang}:{PurePosixPath(audio_path).name}"


def mango_assignments(rows):
    """Sentence key -> train / val / test, exactly 80 / 10 / 10 within each language."""
    sentences_by_lang = {}
    for row in rows:
        lang = row["lang"]
        if lang not in sentences_by_lang:
            sentences_by_lang[lang] = set()
        sentences_by_lang[lang].add(mango_stimulus(row["audio_path"], lang))
    assignments = {}
    for lang in sentences_by_lang:
        assignments.update(rank_buckets(sentences_by_lang[lang]))
    return assignments


def mango_split(row, version, assignments):
    """The split of one MANGO row."""
    bucket = assignments[mango_stimulus(row["audio_path"], row["lang"])]
    if version == "tamil_out" and row["lang"] == "ta":
        if bucket == "test":
            return "test"
        return "test_extra"
    return bucket


def split_for(dataset, row, version, mango_assign=None):
    """The split of one row of any dataset."""
    if version not in VERSIONS:
        raise ValueError(f"unknown version {version!r}")
    if dataset == "speecharena":
        return "test"
    if dataset == "mango":
        return mango_split(row, version, mango_assign)
    # an unknown official split name raises KeyError, on purpose
    return OFFICIAL[dataset][row["source_split"]]


def counts_by_lang_and_split(df):
    """{"lang:split": number of rows}."""
    counts = {}
    for (lang, split), n in df.groupby(["lang", "split"]).size().items():
        counts[f"{lang}:{split}"] = int(n)
    return counts


def mango_checks(df, checks):
    """Leakage checks for MANGO: no sentence may be in two splits."""
    import pandas as pd
    keys = []
    for audio_path, lang in zip(df["audio_path"], df["lang"]):
        keys.append(mango_stimulus(audio_path, lang))
    sentences = pd.DataFrame({"lang": df["lang"], "key": keys, "split": df["split"]})
    splits_per_sentence = sentences.groupby("key")["split"].nunique()
    checks["mango_sentences_in_more_than_one_split"] = int((splits_per_sentence > 1).sum())
    one_row_per_sentence = sentences.drop_duplicates(["key"])
    checks["mango_sentences_per_lang_split"] = counts_by_lang_and_split(one_row_per_sentence)


def speechjudge_checks(df, checks):
    """Leakage checks for SpeechJudge: how many test sentences also appear in train."""
    train_sentences = set(df.loc[df["split"] == "train", "sentence_id"])
    test_sentences = set(df.loc[df["split"] == "test", "sentence_id"])
    test_rows = df[df["split"] == "test"]
    checks["speechjudge_test_sentences_also_in_train"] = len(train_sentences & test_sentences)
    checks["speechjudge_test_pairs_with_sentence_in_train"] = int(test_rows["sentence_id"].isin(train_sentences).sum())
    checks["speechjudge_test_distinct_sentences"] = int(test_rows["sentence_id"].nunique())


def build(root, versions, force=False):
    """Write the split files and the manifest for each version."""
    import pandas as pd
    source = Path(root) / "_harmonized"
    for version in versions:
        out = Path(root) / "_splits" / version
        manifest_path = out / "manifest.json"
        if manifest_path.exists() and not force:
            print(f"{version}: already frozen ({manifest_path}); use --force to rebuild")
            continue
        out.mkdir(parents=True, exist_ok=True)
        manifest = {
            "version": version,
            "rules": RULES,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "tables": {},
            "checks": {},
        }
        pair_splits = {}   # dataset -> {pair_id: split}, so votes get the split of their pair
        for table, (dataset, id_column, kind) in TABLES.items():
            path = source / f"{table}.parquet"
            if not path.exists():
                print(f"{version}: {table} not built yet, skipped")
                continue
            df = pd.read_parquet(path)
            if kind == "votes":
                df["split"] = df["pair_id"].map(pair_splits[dataset])
            else:
                records = df.to_dict("records")
                assignments = None
                if dataset == "mango":
                    assignments = mango_assignments(records)
                splits = []
                for record in records:
                    splits.append(split_for(dataset, record, version, assignments))
                df["split"] = splits
            if kind == "pairs":
                pair_splits[dataset] = dict(zip(df["pair_id"], df["split"]))

            unknown = set(df["split"]) - set(SPLIT_NAMES)
            if df["split"].isna().any() or unknown:
                raise ValueError(f"{version}/{table}: missing or unknown split values {set(df['split'])}")

            split_path = out / f"{table}.parquet"
            tmp = out / f"{table}.parquet.tmp"
            df[[id_column, "split"]].to_parquet(tmp, index=False)
            tmp.replace(split_path)

            counts = {}
            for split, n in df["split"].value_counts().items():
                counts[str(split)] = int(n)
            entry = {"rows": len(df), "by_split": counts}
            if "lang" in df:
                entry["by_lang_split"] = counts_by_lang_and_split(df)
            entry["sha256"] = file_hash(split_path)
            manifest["tables"][table] = entry

            if dataset == "mango":
                mango_checks(df, manifest["checks"])
            if table == "speechjudge_pairs":
                speechjudge_checks(df, manifest["checks"])
            print(f"{version}: {table} -> {counts}")

        save_json(manifest_path, manifest)
        print(f"{version}: frozen, manifest {manifest_path}; checks {manifest['checks']}")


def main():
    parser = argparse.ArgumentParser(description="Freeze the train / val / test splits.")
    parser.add_argument("--root", required=True, help="the datasets folder")
    parser.add_argument("--versions", default=",".join(VERSIONS))
    parser.add_argument("--force", action="store_true", help="rebuild even if already frozen")
    args = parser.parse_args()
    versions = [version for version in args.versions.split(",") if version]
    build(Path(args.root).expanduser(), versions, args.force)


if __name__ == "__main__":
    main()
