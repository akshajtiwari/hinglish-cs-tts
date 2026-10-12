"""Step 2.2 check (read-only): missing audio in the exam data.
(a) Do different vote rows of one SpeechArenaBench item carry the same two clips?
(b) Are the empty rows empty in the ORIGINAL Hugging Face dataset too (not a fault of our filtered copy)?
(c) Does MANGO release audio for the VITS-R system at all?
Run on the server with the hinglishtts venv (needs huggingface_hub, pyarrow, pandas), from the datasets folder.
"""
import hashlib
from pathlib import Path

import pandas as pd
import pyarrow.parquet
from huggingface_hub import HfApi
from huggingface_hub import HfFileSystem


def has_bytes(audio):
    """True if a parquet audio cell holds audio bytes."""
    return bool(audio) and bool(audio.get("bytes"))


# (a) hash the audio of every vote row, grouped by item
items = {}
for path in sorted(Path("speecharena_hi_AB").glob("*.parquet")):
    parquet_file = pyarrow.parquet.ParquetFile(path)
    columns = ["academic_prompt_id", "model_a", "model_b", "audio_a", "audio_b"]
    for batch in parquet_file.iter_batches(columns=columns, batch_size=64):
        for row in batch.to_pylist():
            key = f"{row['academic_prompt_id']}|{row['model_a']}|{row['model_b']}"
            if key not in items:
                items[key] = {"a": set(), "b": set(), "rows": 0}
            items[key]["rows"] += 1
            if has_bytes(row["audio_a"]):
                items[key]["a"].add(hashlib.sha1(row["audio_a"]["bytes"]).hexdigest())
            if has_bytes(row["audio_b"]):
                items[key]["b"].add(hashlib.sha1(row["audio_b"]["bytes"]).hexdigest())

multi = {}
different = {}
for key, item in items.items():
    if item["rows"] > 1:
        multi[key] = item
        if len(item["a"]) > 1 or len(item["b"]) > 1:
            different[key] = item
print("(a) items with 2+ vote rows:", len(multi), "| items whose audio differs between vote rows:", len(different))
for key in list(different)[:3]:
    item = different[key]
    print("    ", key, "distinct A:", len(item["a"]), "distinct B:", len(item["b"]), "rows:", item["rows"])

# (b) look at the same rows in the original dataset; only the batches up to the wanted row are downloaded
hf_files = HfFileSystem()
for shard, wanted_row in [("val-00013-of-00070.parquet", 0), ("val-00060-of-00070.parquet", 15), ("val-00050-of-00070.parquet", 181)]:
    with hf_files.open(f"datasets/ai4bharat/SpeechArenaBench/hi/{shard}", "rb") as remote_file:
        parquet_file = pyarrow.parquet.ParquetFile(remote_file)
        rows_seen = 0
        for batch in parquet_file.iter_batches(columns=["model_a", "model_b", "audio_a", "audio_b"], batch_size=64):
            batch_rows = batch.to_pylist()
            if wanted_row < rows_seen + len(batch_rows):
                row = batch_rows[wanted_row - rows_seen]
                empty_a = not has_bytes(row["audio_a"])
                empty_b = not has_bytes(row["audio_b"])
                print(f"(b) original {shard} row {wanted_row}: {row['model_a']} vs {row['model_b']} | "
                      f"audio_a empty: {empty_a} | audio_b empty: {empty_b}")
                break
            rows_seen += len(batch_rows)

# (c) MANGO: is there any VITS-R audio in the released files?
repo_files = HfApi().list_repo_files("ai4bharat/MANGO", repo_type="dataset")
vits_r_files = [name for name in repo_files if "vits-r" in name.lower() or "vits_r" in name.lower()]
system_folders = set()
for name in repo_files:
    if name.startswith("audios/") and name.count("/") >= 3:
        system_folders.add(name.split("/")[2])
print("(c) MANGO repo files mentioning VITS-R:", len(vits_r_files), "| system folders:", sorted(system_folders))
mango = pd.read_csv("mango/csvs/hindi_extended.csv")
print("    hindi_extended: VITS-R ratings", int(mango["VITS-R_Score"].notna().sum()),
      "| distinct VITS-R audio files referenced:", mango["VITS-R_Audio"].nunique())
