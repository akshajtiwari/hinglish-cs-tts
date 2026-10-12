"""Step 2.2 check (read-only): do different vote rows of one SpeechArenaBench item contain different SOUND,
or only different file bytes (the same waveform saved twice)? Decodes clip A and clip B of two vote rows
for up to 40 items and compares format, sample rate, duration and the waveform itself.
Run on the server inside tmux with the baselines venv, from the datasets folder.
"""
import io
import tempfile
from pathlib import Path

import librosa
import numpy
import pyarrow.parquet
import soundfile


def decode(audio):
    """Decode audio bytes to a mono waveform. soundfile reads from memory; librosa needs a real file."""
    data = audio["bytes"]
    try:
        wav, sr = soundfile.read(io.BytesIO(data), dtype="float32", always_2d=True)
        return wav.mean(axis=1), sr
    except Exception:
        suffix = Path(audio.get("path") or "x.mp3").suffix
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(data)
            temp_file.flush()
            wav, sr = librosa.load(temp_file.name, sr=None, mono=True)
        return wav, sr


def has_both_clips(row):
    """True if both audio cells of a row hold audio bytes."""
    for column in ["audio_a", "audio_b"]:
        if not row[column] or not row[column].get("bytes"):
            return False
    return True


def count_items_with_two_rows(rows_by_item):
    """How many items have at least two vote rows."""
    count = 0
    for rows in rows_by_item.values():
        if len(rows) >= 2:
            count += 1
    return count


def suffix_of(audio):
    """The file extension of the original audio name, or '' when unknown."""
    return Path(audio.get("path") or "?").suffix


rows_by_item = {}
columns = ["academic_prompt_id", "model_a", "model_b", "audio_a", "audio_b", "user_id"]
for path in sorted(Path("speecharena_hi_AB").glob("*.parquet")):
    parquet_file = pyarrow.parquet.ParquetFile(path)
    for batch in parquet_file.iter_batches(columns=columns, batch_size=64):
        for row in batch.to_pylist():
            if has_both_clips(row):
                key = f"{row['academic_prompt_id']}|{row['model_a']}|{row['model_b']}"
                if key not in rows_by_item:
                    rows_by_item[key] = []
                rows_by_item[key].append(row)
    if count_items_with_two_rows(rows_by_item) >= 40:
        break

items_to_compare = []
for key, rows in rows_by_item.items():
    if len(rows) >= 2:
        items_to_compare.append((key, rows))

same_wave = 0
different_wave = 0
for key, rows in items_to_compare[:40]:
    row1 = rows[0]
    row2 = rows[1]
    lines = []
    for column in ["audio_a", "audio_b"]:
        wav1, sr1 = decode(row1[column])
        wav2, sr2 = decode(row2[column])
        n = min(len(wav1), len(wav2))
        same = False
        if sr1 == sr2 and abs(len(wav1) - len(wav2)) <= 1 and n > 0:
            same = float(numpy.max(numpy.abs(wav1[:n] - wav2[:n]))) < 1e-3
        corr = float("nan")
        if n > 10 and sr1 == sr2:
            corr = float(numpy.corrcoef(wav1[:n], wav2[:n])[0, 1])
        lines.append(f"{column}: {suffix_of(row1[column])} {sr1}Hz {len(wav1) / sr1:.2f}s vs {suffix_of(row2[column])} "
                     f"{sr2}Hz {len(wav2) / sr2:.2f}s | same waveform: {same} | corr {corr:.3f}")
        if same:
            same_wave += 1
        else:
            different_wave += 1
    print(key.split("|", 1)[1], "| raters", row1["user_id"], row2["user_id"])
    for line in lines:
        print("    ", line)
print(f"\nclip comparisons with the same waveform: {same_wave}, different: {different_wave}")
