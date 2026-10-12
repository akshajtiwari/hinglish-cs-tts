"""Step 2.2: prepare the exam (test) audio and the exam lists for the baseline scorers.

Reads the raw data without changing it; everything is written under datasets/_exam/.
Writes are atomic, and a rerun skips audio that is already extracted.
Split version: tamil_out (its test sets contain everything: MANGO Tamil test + test_extra).

Outputs
  _exam/audio/{speechjudge,speecharena_votes,somos}/...  audio taken from parquet bytes or from SOMOS's inner audios.zip
                                                         (BVCC and MANGO audio is used where it already is)
  _exam/clips_{bvcc,somos,mango}.csv    one row per clip (and MANGO variant)
  _exam/pairs_speechjudge.csv           one row per pair
  _exam/votes_speecharena.csv           one row per VOTE (every vote heard its own fresh synthesis, so the vote is the exam unit)
  _exam/audio_list.csv                  every unique audio path to score (audio_status ok only)
audio_status: ok | missing_in_source (no audio bytes in the released row) | not_released (the dataset rates a clip
it does not ship, e.g. MANGO VITS-R). Missing audio is never guessed; it is counted and left out of scoring.

Run (server, baselines venv):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step2_baselines/prepare_exam_audio.py --root ~/projects/hinglish-cs-tts/datasets
"""
import argparse
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet

from switchmos import files

VERSION = "tamil_out"
TEST_SPLITS = ["test", "test_extra"]


def write_bytes(path, data):
    """Write audio bytes atomically; skip the file if it already exists with the same size."""
    if path.exists() and path.stat().st_size == len(data):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def file_extension(audio):
    """The extension of the original audio file name, or .wav if there is none."""
    name = audio.get("path") or "x.wav"
    extension = Path(name).suffix
    if extension == "":
        extension = ".wav"
    return extension


def has_bytes(audio):
    """True if a parquet audio cell holds audio bytes."""
    return bool(audio) and bool(audio.get("bytes"))


def table_with_split(root, table, id_col):
    """Read a harmonised table and add the frozen split of each row."""
    df = pd.read_parquet(root / "_harmonized" / f"{table}.parquet")
    df = df.drop(columns=["split"], errors="ignore")   # votes have no split column
    splits = pd.read_parquet(root / "_splits" / VERSION / f"{table}.parquet")
    return df.merge(splits, on=id_col, how="inner")


def rating_clips(root, name, exam):
    """One row per test clip of a rating dataset, with its mean score."""
    ratings = table_with_split(root, f"{name}_ratings", "rating_id")
    ratings = ratings[ratings["split"].isin(TEST_SPLITS)].copy()
    ratings["variant"] = ratings["variant"].fillna("")
    clips = ratings.groupby(["clip_id", "variant"], as_index=False).agg(
        audio_path=("audio_path", "first"),
        mos=("score", "mean"),
        n_ratings=("score", "size"),
        system=("system_id", "first"),
        lang=("lang", "first"),
        split=("split", "first"),
    )
    paths = []
    for clip_id, audio_path in zip(clips["clip_id"], clips["audio_path"]):
        if name == "bvcc":
            paths.append(str(root / "bvcc" / "main" / audio_path))
        elif name == "mango":
            paths.append(str(root / "mango" / audio_path))
        else:
            paths.append(str(exam / "audio" / "somos" / f"{clip_id}.wav"))
    clips["path"] = paths
    return clips


def extract_somos(root, exam, clip_ids):
    """Copy SOMOS's inner audios.zip out once, then extract the test clips from it."""
    inner_copy = exam / "somos_audios.zip"
    if not inner_copy.exists():
        # reading from a zip inside a zip is slow, so the inner zip is copied out first
        with zipfile.ZipFile(root / "somos" / "somos.zip") as outer:
            member = None
            for name in outer.namelist():
                if name.endswith("audios.zip"):
                    member = name
                    break
            tmp = inner_copy.with_name(inner_copy.name + ".tmp")
            with outer.open(member) as source:
                with open(tmp, "wb") as target:
                    shutil.copyfileobj(source, target, 4 * 1024 * 1024)
            tmp.replace(inner_copy)
    wanted = set(clip_ids)
    with zipfile.ZipFile(inner_copy) as inner:
        for name in inner.namelist():
            stem = Path(name).stem
            if name.endswith(".wav") and stem in wanted:
                write_bytes(exam / "audio" / "somos" / f"{stem}.wav", inner.read(name))
    missing = 0
    for clip_id in wanted:
        if not (exam / "audio" / "somos" / f"{clip_id}.wav").exists():
            missing += 1
    print(f"somos: {len(wanted) - missing} clips extracted, {missing} missing")


def speechjudge_pairs(root, exam):
    """The SpeechJudge test pairs, with their two clips extracted to disk."""
    pairs = table_with_split(root, "speechjudge_pairs", "pair_id")
    train_sentences = set(pairs.loc[pairs["split"] == "train", "sentence_id"])
    test = pairs[pairs["split"] == "test"].copy()
    needed = set(test["pair_id"])
    paths_a = {}
    paths_b = {}
    for path in sorted((root / "speechjudge").rglob("test-*.parquet")):
        # the parquet files hold the audio bytes, so they are read in small batches
        parquet_file = pyarrow.parquet.ParquetFile(path)
        for batch in parquet_file.iter_batches(columns=["index", "audioA", "audioB"], batch_size=64):
            for row in batch.to_pylist():
                pair_id = f"speechjudge:{row['index']}"
                if pair_id not in needed:
                    continue
                if has_bytes(row["audioA"]):
                    out = exam / "audio" / "speechjudge" / f"{row['index']}_a{file_extension(row['audioA'])}"
                    write_bytes(out, row["audioA"]["bytes"])
                    paths_a[pair_id] = str(out)
                if has_bytes(row["audioB"]):
                    out = exam / "audio" / "speechjudge" / f"{row['index']}_b{file_extension(row['audioB'])}"
                    write_bytes(out, row["audioB"]["bytes"])
                    paths_b[pair_id] = str(out)
    test["path_a"] = [paths_a.get(pair_id) for pair_id in test["pair_id"]]
    test["path_b"] = [paths_b.get(pair_id) for pair_id in test["pair_id"]]
    test["sentence_in_train"] = test["sentence_id"].isin(train_sentences)
    print(f"speechjudge: {test['path_a'].notna().sum()} of {len(test)} test pairs extracted; "
          f"{int(test['sentence_in_train'].sum())} share their sentence with train")
    return test


def speecharena_votes(root, exam):
    """One row per vote, with that vote's own two clips extracted to disk."""
    votes = table_with_split(root, "speecharena_votes", "vote_id")
    items = pd.read_parquet(root / "_harmonized" / "speecharena_pairs.parquet",
                            columns=["pair_id", "system_a", "system_b", "mixed", "lang", "sentence_id"])
    votes = votes.merge(items, on="pair_id", how="left")
    # source_row is "<shard>:<row>" of the vote's own row in our copy of the data
    vote_of_row = dict(zip(votes["source_row"], votes["vote_id"]))
    paths_a = {}
    paths_b = {}
    for path in sorted((root / "speecharena_hi_AB").glob("*.parquet")):
        parquet_file = pyarrow.parquet.ParquetFile(path)
        for batch in parquet_file.iter_batches(columns=["src_shard", "src_row", "audio_a", "audio_b"], batch_size=32):
            for row in batch.to_pylist():
                vote_id = vote_of_row.get(f"{row['src_shard']}:{row['src_row']}")
                if vote_id is None:
                    continue
                # "speecharena:<hash>:<n>" -> "<hash>_<n>"
                key = vote_id.split(":", 1)[1].replace(":", "_")
                if has_bytes(row["audio_a"]):
                    out = exam / "audio" / "speecharena_votes" / f"{key}_a{file_extension(row['audio_a'])}"
                    write_bytes(out, row["audio_a"]["bytes"])
                    paths_a[vote_id] = str(out)
                if has_bytes(row["audio_b"]):
                    out = exam / "audio" / "speecharena_votes" / f"{key}_b{file_extension(row['audio_b'])}"
                    write_bytes(out, row["audio_b"]["bytes"])
                    paths_b[vote_id] = str(out)
    votes["path_a"] = [paths_a.get(vote_id) for vote_id in votes["vote_id"]]
    votes["path_b"] = [paths_b.get(vote_id) for vote_id in votes["vote_id"]]
    both = votes["path_a"].notna() & votes["path_b"].notna()
    statuses = []
    for has_both in both:
        if has_both:
            statuses.append("ok")
        else:
            statuses.append("missing_in_source")
    votes["audio_status"] = statuses
    votes = votes.rename(columns={"vote": "label"})
    missing_labels = votes.loc[~both, "label"].value_counts().to_dict()
    print(f"speecharena: {int(both.sum())} of {len(votes)} votes have both clips; "
          f"missing_in_source {int((~both).sum())} (labels {missing_labels})")
    return votes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).expanduser()
    exam = root / "_exam"
    exam.mkdir(parents=True, exist_ok=True)
    all_paths = []

    for name in ["bvcc", "mango", "somos"]:
        clips = rating_clips(root, name, exam)
        if name == "somos":
            extract_somos(root, exam, clips["clip_id"].unique())
        # a dataset may rate a clip it does not ship (MANGO VITS-R): count it, never guess it
        statuses = []
        for path in clips["path"]:
            if Path(path).exists():
                statuses.append("ok")
            else:
                statuses.append("not_released")
        clips["audio_status"] = statuses
        files.save_csv(clips, exam / f"clips_{name}.csv")
        all_paths.extend(clips.loc[clips["audio_status"] == "ok", "path"])
        print(f"{name}: {len(clips)} exam clips ({clips['split'].value_counts().to_dict()}), "
              f"audio {clips['audio_status'].value_counts().to_dict()}")

    pair_columns = ["pair_id", "path_a", "path_b", "label", "n_votes", "n_decided", "agreement",
                    "system_a", "system_b", "mixed", "lang", "sentence_id", "sentence_in_train"]
    pairs = speechjudge_pairs(root, exam)[pair_columns]
    files.save_csv(pairs, exam / "pairs_speechjudge.csv")
    all_paths.extend(pairs["path_a"].dropna())
    all_paths.extend(pairs["path_b"].dropna())

    vote_columns = ["vote_id", "pair_id", "path_a", "path_b", "label", "tie_kind", "system_a",
                    "system_b", "mixed", "lang", "sentence_id", "rater_id", "audio_status"]
    votes = speecharena_votes(root, exam)[vote_columns]
    files.save_csv(votes, exam / "votes_speecharena.csv")
    ok = votes["audio_status"] == "ok"
    all_paths.extend(votes.loc[ok, "path_a"])
    all_paths.extend(votes.loc[ok, "path_b"])

    audio_list = pd.DataFrame({"path": sorted(set(all_paths))})
    missing = 0
    for path in audio_list["path"]:
        if not Path(path).exists():
            missing += 1
    files.save_csv(audio_list, exam / "audio_list.csv")
    print(f"audio_list: {len(audio_list)} unique files, {missing} missing on disk")


if __name__ == "__main__":
    main()
