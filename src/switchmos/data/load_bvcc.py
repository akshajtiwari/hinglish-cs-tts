"""BVCC loader (VoiceMOS 2022 main track): one row per single rating.

DATA/sets/TRAINSET, DEVSET and TESTSET hold one rating per line:
    sysID,uttID,rating,ignore,listenerinfo
listenerinfo looks like {}_AGERANGE_LISTENERID_GENDER_..., so the listener id is its third "_" part.
Ratings are MOS 1-5. The dataset's own split names: train, dev, test.
"""
from pathlib import Path

SPLIT_FILES = {"train": "TRAINSET", "dev": "DEVSET", "test": "TESTSET"}


def rater_from_info(info):
    """The listener id: the third "_" part of listenerinfo, or the whole text if there is none."""
    parts = info.split("_")
    if len(parts) >= 3 and parts[2]:
        return parts[2]
    return info


def convert_lines(lines, source_split):
    """Turn the lines of one BVCC set file into rating rows."""
    rows = []
    # n counts every line, blank ones too, so rating_id stays the line number of the file
    for n, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        fields = line.split(",")
        if len(fields) < 5:
            raise ValueError(f"BVCC {source_split} line {n}: expected 5 comma separated fields, got {len(fields)}: {line[:80]!r}")
        system_id = fields[0]
        utterance = fields[1]
        rating = float(fields[2])
        listener_info = ",".join(fields[4:])
        rows.append({
            "rating_id": f"bvcc:{source_split}:{n}",
            "dataset": "bvcc",
            "split": "unassigned",
            "source_split": source_split,
            "clip_id": utterance,
            "audio_path": f"DATA/wav/{utterance}",
            "sr": 16000,
            "dur_s": None,
            "transcript": None,
            "lang": "en",
            "mixed": False,
            "system_id": system_id,
            "rater_id": rater_from_info(listener_info),
            "rater_native": None,
            "rater_reliability": None,
            "label_type": "mos",
            "score": rating,
            "score_min": 1.0,
            "score_max": 5.0,
            "page_id": None,
            "variant": None,
        })
    return rows


def load(main_dir):
    """Read the three BVCC set files and return all rating rows."""
    rows = []
    for source_split, file_name in SPLIT_FILES.items():
        path = Path(main_dir) / "DATA" / "sets" / file_name
        with open(path, encoding="utf-8") as f:
            rows.extend(convert_lines(f, source_split))
    return rows
