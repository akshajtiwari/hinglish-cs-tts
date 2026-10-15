"""Read-only SAB identity audit and basic audio measurements; no model inference.

Run in tmux with the existing baselines environment. Writes only --out.
Quiet frames are energy measurements, not speech/pause or pronunciation labels.
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf

from switchmos import files
from switchmos.data.load_speecharena import classify, is_mixed, make_pair_id


def read_csv(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def save_rows(path, rows):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def measure(path):
    wave, rate = sf.read(path, dtype="float32", always_2d=True)
    if not len(wave) or not np.isfinite(wave).all():
        raise ValueError("Empty or non-finite audio: " + path)
    mono = wave.mean(axis=1)
    frame_size = max(1, round(rate * 0.020))
    frames = []
    for start in range(0, len(mono), frame_size):
        piece = mono[start:start + frame_size].astype("float64")
        frames.append(float(np.sqrt(np.mean(piece * piece))))
    energy = np.array(frames)
    relative_threshold = float(energy.max()) * 10 ** (-35 / 20)
    quiet = energy <= relative_threshold
    voiced = np.flatnonzero(~quiet)
    longest = 0
    current = 0
    for flag in quiet:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    leading = len(mono) / rate
    trailing = leading
    if len(voiced):
        leading = min(len(mono) / rate, int(voiced[0]) * frame_size / rate)
        trailing = max(0.0, (len(mono) - (int(voiced[-1]) + 1) * frame_size) / rate)
    return {
        "path": path, "sha256": files.file_hash(path), "seconds": len(wave) / rate,
        "sample_rate": rate, "channels": wave.shape[1],
        "peak": float(np.max(np.abs(wave))),
        "rms": float(np.sqrt(np.mean(mono.astype("float64") ** 2))),
        "near_full_scale_fraction": float(np.mean(np.abs(wave) >= 0.999)),
        "quiet_relative_fraction": float(quiet.mean()),
        "quiet_absolute_fraction": float(np.mean(energy <= 10 ** (-45 / 20))),
        "leading_quiet_seconds": leading, "trailing_quiet_seconds": trailing,
        "longest_quiet_seconds": min(len(mono) / rate, longest * frame_size / rate),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--listening-sheet", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    exam = read_csv(args.root / "_exam/votes_speecharena.csv")
    exam_by_id = {row["vote_id"]: row for row in exam}
    assert len(exam_by_id) == len(exam), "Duplicate vote IDs"
    votes = pq.read_table(args.root / "_harmonized/speecharena_votes.parquet").to_pylist()
    pairs = pq.read_table(args.root / "_harmonized/speecharena_pairs.parquet").to_pylist()
    pair_by_id = {row["pair_id"]: row for row in pairs}
    save_rows(args.out / "sentences.csv", [
        {"pair_id": row["pair_id"], "sentence_id": row["sentence_id"], "transcript": row["transcript"]}
        for row in pairs])
    by_source = {}
    for vote in votes:
        if vote["vote_id"] in exam_by_id:
            assert vote["source_row"] not in by_source, "Duplicate source-row mapping"
            by_source[vote["source_row"]] = vote
    selected = {row["vote_id"] for row in read_csv(args.listening_sheet)}
    errors = []
    seen = set()
    raw_audio_checks = []
    selected_sources = set()
    for source, vote in by_source.items():
        if vote["vote_id"] in selected:
            selected_sources.add(source)
    columns = ["src_shard", "src_row", "academic_prompt_id", "sentence",
               "model_a", "model_b", "preference_model"]
    for shard in sorted((args.root / "speecharena_hi_AB").glob("*.parquet")):
        for row in pq.read_table(shard, columns=columns).to_pylist():
            source = f"{row['src_shard']}:{row['src_row']}"
            if source not in by_source:
                continue
            vote = by_source[source]
            identity = vote["vote_id"]
            if identity in seen:
                errors.append("Repeated raw vote: " + identity)
            seen.add(identity)
            actual = exam_by_id[identity]
            pair = pair_by_id[vote["pair_id"]]
            label, tie = classify(row["preference_model"], row["model_a"], row["model_b"])
            checks = [actual["label"] == label, (actual["tie_kind"] or None) == tie,
                      actual["pair_id"] == make_pair_id(row),
                      actual["system_a"] == row["model_a"], actual["system_b"] == row["model_b"],
                      (actual["mixed"] == "True") == is_mixed(row["sentence"]),
                      pair["transcript"] == row["sentence"],
                      actual["sentence_id"] == str(pair["sentence_id"])]
            if not all(checks):
                errors.append("Metadata mismatch: " + identity)
        # Byte equality verifies the selected listening votes use their own source audio.
        for batch in pq.ParquetFile(shard).iter_batches(
                columns=["src_shard", "src_row", "audio_a", "audio_b"], batch_size=8):
            for row in batch.to_pylist():
                source = f"{row['src_shard']}:{row['src_row']}"
                if source not in selected_sources:
                    continue
                identity = by_source[source]["vote_id"]
                actual = exam_by_id[identity]
                for side in ["a", "b"]:
                    raw = row["audio_" + side]["bytes"]
                    raw_hash = hashlib.sha256(raw).hexdigest()
                    disk_hash = files.file_hash(actual["path_" + side])
                    raw_audio_checks.append({"vote_id":identity, "side":side,
                                             "raw_sha256":raw_hash, "exam_sha256":disk_hash,
                                             "matches":raw_hash == disk_hash})
                    if raw_hash != disk_hash:
                        errors.append("Raw audio mismatch: " + identity + " " + side)
        print("Audited source shard:", shard.name, flush=True)
    if seen != set(exam_by_id):
        errors.append("Not all exam votes found in raw source")
    if len(raw_audio_checks) != 2 * len(selected):
        errors.append("Not all selected audio sides checked")
    save_rows(args.out / "raw_audio_checks.csv", raw_audio_checks)
    files.save_json(args.out / "identity_audit.json", {
        "exam_votes":len(exam), "raw_votes_checked":len(seen),
        "selected_raw_audio_checks":len(raw_audio_checks), "errors":errors})
    if errors:
        raise ValueError(str(errors))
    paths = set()
    for row in exam:
        if row["audio_status"] == "ok":
            paths.add(row["path_a"])
            paths.add(row["path_b"])
    measured = []
    audio_errors = []
    for index, path in enumerate(sorted(paths)):
        try:
            measured.append(measure(path))
        except Exception as error:
            audio_errors.append({"path":path, "error":str(error)})
        if (index + 1) % 500 == 0:
            print("Audio files checked:", index + 1, "of", len(paths), flush=True)
            save_rows(args.out / "audio_features.csv", measured)
            files.save_json(args.out / "audio_errors.json", audio_errors)
    save_rows(args.out / "audio_features.csv", measured)
    files.save_json(args.out / "audio_errors.json", audio_errors)
    files.save_json(args.out / "collection_manifest.json", {
        "expected_audio_files":len(paths), "measured":len(measured), "errors":len(audio_errors),
        "frame_seconds":0.020, "relative_quiet_db_below_peak_frame_rms":35,
        "absolute_quiet_dbfs":-45, "near_full_scale_amplitude":0.999,
        "script_sha256":files.file_hash(__file__), "numpy":np.__version__, "soundfile":sf.__version__,
        "note":"Energy proxies only, not speech detection or causal findings. Original audio unchanged."})
    print("DONE", len(measured), "audio files;", len(audio_errors), "errors", flush=True)


if __name__ == "__main__":
    main()
