"""SOMOS loader: single-clip MOS ratings with listener ids.

The score files are read straight from inside somos.zip (nothing is extracted):
    raw_scores_with_metadata/split1/raw_scores_removed_excess_gt_{trainset,validset,testset}.tsv
The dataset's own split names: train, valid, test.
The audio is inside the nested audios.zip, so audio_path is "audios.zip:<utteranceId>.wav".
"""
import csv
import io
import zipfile

SPLIT_FILES = {
    "train": "raw_scores_with_metadata/split1/raw_scores_removed_excess_gt_trainset.tsv",
    "valid": "raw_scores_with_metadata/split1/raw_scores_removed_excess_gt_validset.tsv",
    "test": "raw_scores_with_metadata/split1/raw_scores_removed_excess_gt_testset.tsv",
}


def convert_lines(lines, source_split):
    """Turn the lines of one SOMOS TSV file (with its header line) into rating rows."""
    rows = []
    reader = csv.DictReader(lines, delimiter="\t")
    for n, row in enumerate(reader):
        reliability = row.get("listenerReliability")
        if reliability in (None, ""):
            reliability = None
        else:
            reliability = float(reliability)
        rows.append({
            "rating_id": f"somos:{source_split}:{n}",
            "dataset": "somos",
            "split": "unassigned",
            "source_split": source_split,
            "clip_id": row["utteranceId"],
            "audio_path": f"audios.zip:{row['utteranceId']}.wav",
            "sr": None,
            "dur_s": None,
            "transcript": None,
            "lang": "en",
            "mixed": False,
            "system_id": row["systemId"],
            "rater_id": row["listenerId"],
            "rater_native": row.get("isNative") == "1",
            "rater_reliability": reliability,
            "label_type": "mos",
            "score": float(row["choice"]),
            "score_min": 1.0,
            "score_max": 5.0,
            "page_id": row.get("testpageId"),
            "variant": None,
        })
    return rows


def load(zip_path):
    """Read the three SOMOS score files from the zip and return all rating rows."""
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        for source_split, member in SPLIT_FILES.items():
            with z.open(member) as raw_file:
                # zip members open as bytes; TextIOWrapper reads them as text lines
                text_file = io.TextIOWrapper(raw_file, encoding="utf-8")
                rows.extend(convert_lines(text_file, source_split))
    return rows
