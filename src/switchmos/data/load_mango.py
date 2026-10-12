"""MANGO loader: MUSHRA listening-test pages.

Each CSV row is one page: one rater scored several systems for one sentence on a 0-100 scale.
We make one rating row per system score.
Columns: Rater_ID, <SYSTEM>_Score and <SYSTEM>_Audio for FS2, VITS, ST2, ANC (anchor), REF (reference);
hindi_extended.csv also has VITS-R and XTTS.
File names: <language>_<variant>.csv, e.g. hindi_mushra_dg_nmr.csv.
"""
import csv
from pathlib import Path

SYSTEMS = ["FS2", "VITS", "ST2", "ANC", "REF", "VITS-R", "XTTS"]
LANGUAGE_CODES = {"hindi": "hi", "tamil": "ta", "english": "en"}
SYSTEM_NAMES = {"ANC": "anchor", "REF": "reference"}


def name_parts(csv_name):
    """'hindi_mushra_dg_nmr.csv' -> ('hi', 'mushra_dg_nmr', 'hindi_mushra_dg_nmr')."""
    stem = Path(csv_name).stem
    language, separator, variant = stem.partition("_")
    return LANGUAGE_CODES[language], variant, stem


def convert_rows(csv_name, csv_rows):
    """Turn the rows of one MANGO CSV file (dicts from csv.DictReader) into rating rows."""
    lang, variant, stem = name_parts(csv_name)
    rows = []
    for n, row in enumerate(csv_rows):
        page_id = f"mango:{stem}:{n}"
        for system in SYSTEMS:
            score = row.get(f"{system}_Score")
            audio = row.get(f"{system}_Audio")
            if score in (None, "") or not audio:
                continue
            rows.append({
                "rating_id": f"{page_id}:{system}",
                "dataset": "mango",
                "split": "unassigned",
                "source_split": None,
                "clip_id": audio,
                "audio_path": audio,
                "sr": None,
                "dur_s": None,
                "transcript": None,
                "lang": lang,
                "mixed": None,
                "system_id": SYSTEM_NAMES.get(system, system),
                "rater_id": str(row["Rater_ID"]),
                "rater_native": None,
                "rater_reliability": None,
                "label_type": "mushra",
                "score": float(score),
                "score_min": 0.0,
                "score_max": 100.0,
                "page_id": page_id,
                "variant": variant,
            })
    return rows


def load(root):
    """Read every CSV in <root>/csvs and return all rating rows."""
    rows = []
    for path in sorted((Path(root) / "csvs").glob("*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            rows.extend(convert_rows(path.name, csv.DictReader(f)))
    return rows
