"""Step 3 pilot, part 1: the training and validation clips, their targets and the SpeechJudge pairs.

Only the train and val splits of version tamil_out are used. Test data and SpeechArenaBench are never written here.
The raw datasets are only read. Everything is written under <root>/_train/:
  audio/speechjudge/<index>_a.<ext>, <index>_b.<ext>   train and val pairs, taken from the parquet audio bytes
  audio/somos/<clip>.wav                              train and val clips, taken from SOMOS's inner audios.zip
  clips.csv     key, dataset, split, path             every clip to encode (BVCC and MANGO audio stay where they are)
  ratings.csv   key, dataset, split, lang, target     one row per rated clip:
                                                      BVCC and SOMOS: mean MOS; MANGO: mean page z-score
  pairs.csv     pair_id, key_a, key_b, label, split, lang, mixed    SpeechJudge pairs with a winner (A or B)
Files already extracted are skipped, so the script can be run again after a stop.

Run (server, CPU):
  PYTHONPATH=src ~/projects/baselines-venv/bin/python scripts/step3_pilot/prepare_training_data.py \
      --root ~/projects/hinglish-cs-tts/datasets
"""
import argparse
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet

from switchmos import files
from switchmos import pilot

VERSION = "tamil_out"
KEEP_SPLITS = ["train", "val"]
# SpeechJudge file names start with the dataset's own split name; dev is our val
SPEECHJUDGE_FILE_SPLITS = ["train", "dev"]


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


def table_with_split(root, table, id_column):
    """Read a harmonised table, add the frozen split of each row, and keep only train and val rows."""
    df = pd.read_parquet(root / "_harmonized" / f"{table}.parquet")
    df = df.drop(columns=["split"], errors="ignore")
    splits = pd.read_parquet(root / "_splits" / VERSION / f"{table}.parquet")
    df = df.merge(splits, on=id_column, how="inner")
    return df[df["split"].isin(KEEP_SPLITS)]


def rating_rows(root, dataset):
    """The train and val ratings of one rating dataset."""
    return table_with_split(root, f"{dataset}_ratings", "rating_id")


def clip_path(root, out, dataset, clip_id, audio_path):
    """Where the audio of one rating clip is on disk."""
    if dataset == "bvcc":
        return root / "bvcc" / "main" / audio_path
    if dataset == "mango":
        return root / "mango" / audio_path
    if dataset == "somos":
        return out / "audio" / "somos" / f"{clip_id}.wav"
    raise ValueError(f"unknown dataset {dataset!r}")


def extract_somos(root, out, clip_ids):
    """Extract the wanted SOMOS clips from the inner audios.zip (copied out once by prepare_exam_audio.py)."""
    inner_copy = root / "_exam" / "somos_audios.zip"
    if not inner_copy.exists():
        # reading from a zip inside a zip is slow, so the inner zip is copied out first
        with zipfile.ZipFile(root / "somos" / "somos.zip") as outer:
            member = None
            for name in outer.namelist():
                if name.endswith("audios.zip"):
                    member = name
                    break
            tmp = inner_copy.with_name(inner_copy.name + ".tmp")
            inner_copy.parent.mkdir(parents=True, exist_ok=True)
            with outer.open(member) as source:
                with open(tmp, "wb") as target:
                    shutil.copyfileobj(source, target, 4 * 1024 * 1024)
            tmp.replace(inner_copy)
    wanted = set(clip_ids)
    with zipfile.ZipFile(inner_copy) as inner:
        for name in inner.namelist():
            stem = Path(name).stem
            if name.endswith(".wav") and stem in wanted:
                write_bytes(out / "audio" / "somos" / f"{stem}.wav", inner.read(name))


def extract_speechjudge(root, out, needed_indexes):
    """Extract both clips of the wanted SpeechJudge pairs. Returns {(index, side): path}."""
    paths = {}
    for file_split in SPEECHJUDGE_FILE_SPLITS:
        for parquet_path in sorted((root / "speechjudge").rglob(f"{file_split}-*.parquet")):
            # the files hold the audio bytes, so they are read in small batches
            parquet_file = pyarrow.parquet.ParquetFile(parquet_path)
            for batch in parquet_file.iter_batches(columns=["index", "audioA", "audioB"], batch_size=64):
                for row in batch.to_pylist():
                    index = row["index"]
                    if index not in needed_indexes:
                        continue
                    for side, column in [("A", "audioA"), ("B", "audioB")]:
                        audio = row[column]
                        if has_bytes(audio):
                            path = out / "audio" / "speechjudge" / f"{index}_{side.lower()}{file_extension(audio)}"
                            write_bytes(path, audio["bytes"])
                            paths[(index, side)] = path
            print(f"  {parquet_path.name}: {len(paths)} clips so far", flush=True)
    return paths


def main():
    parser = argparse.ArgumentParser(description="Training and validation data for the Step 3 pilot.")
    parser.add_argument("--root", required=True, help="the datasets folder")
    args = parser.parse_args()
    root = Path(args.root).expanduser()
    out = root / "_train"

    clip_rows = []
    rating_targets = []

    # rating datasets: one target per clip
    for dataset in ["bvcc", "somos", "mango"]:
        ratings = rating_rows(root, dataset)
        if dataset == "somos":
            extract_somos(root, out, set(ratings["clip_id"]))
        keys = []
        for clip_id in ratings["clip_id"]:
            keys.append(f"{dataset}:{clip_id}")
        if dataset == "mango":
            targets = pilot.page_normalised_targets(keys, list(ratings["page_id"]), list(ratings["score"]))
        else:
            targets = pilot.clip_mean_targets(keys, list(ratings["score"]))
        first_rows = ratings.drop_duplicates("clip_id")
        missing = 0
        for row in first_rows.to_dict("records"):
            key = f"{dataset}:{row['clip_id']}"
            path = clip_path(root, out, dataset, row["clip_id"], row["audio_path"])
            if not path.exists():
                missing += 1
                continue
            clip_rows.append({"key": key, "dataset": dataset, "split": row["split"], "path": str(path)})
            rating_targets.append({"key": key, "dataset": dataset, "split": row["split"],
                                   "lang": row["lang"], "target": targets[key]})
        print(f"{dataset}: {len(first_rows) - missing} clips, {missing} without audio", flush=True)

    # SpeechJudge pairs with a winner
    pairs = table_with_split(root, "speechjudge_pairs", "pair_id")
    pairs = pairs[pairs["label"].isin(["A", "B"])]
    indexes = []
    for pair_id in pairs["pair_id"]:
        indexes.append(int(pair_id.split(":")[1]))
    pairs = pairs.assign(index=indexes)
    print(f"speechjudge: extracting {len(pairs)} train and val pairs", flush=True)
    paths = extract_speechjudge(root, out, set(indexes))
    pair_rows = []
    dropped = 0
    for row in pairs.to_dict("records"):
        index = row["index"]
        if (index, "A") not in paths or (index, "B") not in paths:
            dropped += 1
            continue
        key_a = f"speechjudge:{index}:A"
        key_b = f"speechjudge:{index}:B"
        clip_rows.append({"key": key_a, "dataset": "speechjudge", "split": row["split"], "path": str(paths[(index, "A")])})
        clip_rows.append({"key": key_b, "dataset": "speechjudge", "split": row["split"], "path": str(paths[(index, "B")])})
        pair_rows.append({"pair_id": row["pair_id"], "key_a": key_a, "key_b": key_b, "label": row["label"],
                          "split": row["split"], "lang": row["lang"], "mixed": row["mixed"]})
    print(f"speechjudge: {len(pair_rows)} pairs kept, {dropped} without both clips", flush=True)

    clips = pd.DataFrame(clip_rows).sort_values("key")
    assert clips["key"].is_unique, "every clip key must appear once"
    files.save_csv(clips, out / "clips.csv")
    files.save_csv(pd.DataFrame(rating_targets).sort_values("key"), out / "ratings.csv")
    files.save_csv(pd.DataFrame(pair_rows).sort_values("pair_id"), out / "pairs.csv")
    print(f"written: {len(clips)} clips, {len(rating_targets)} rated clips, {len(pair_rows)} pairs in {out}")
    print("clips per dataset and split:")
    print(clips.groupby(["dataset", "split"]).size().to_string())


if __name__ == "__main__":
    main()
