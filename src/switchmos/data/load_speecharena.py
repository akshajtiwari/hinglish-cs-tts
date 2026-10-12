"""SpeechArenaBench loader (Hindi, allowed systems only): one source row is one rater's vote on a pair.

A vote (preference_model) is one of:
    one system name               -> that system wins (A or B)
    two system names joined by ", " -> both clips are good -> TIE, tie_kind both_good
    "Tie / No Preference"           -> TIE, tie_kind no_preference
The pair label is the majority of the A and B votes; equal counts give TIE.
Free-text comments are dropped on purpose; only the six 1-5 axis ratings are kept, as JSON.
The "language" field is "hi" everywhere, so a sentence counts as mixed when it has
both Devanagari and Latin letters.
"""
import hashlib
import json
from pathlib import Path

COLUMNS = ["academic_prompt_id", "sentence", "model_a", "model_b", "user_id", "gender", "preference_model",
           "fine_grained_eval", "src_shard", "src_row"]


def is_mixed(sentence):
    """True when the sentence has both a Devanagari letter and a Latin (a-z, A-Z) letter."""
    has_devanagari = False
    has_latin = False
    for ch in sentence or "":
        if "ऀ" <= ch <= "ॿ":
            has_devanagari = True
        if ch.isascii() and ch.isalpha():
            has_latin = True
    return has_devanagari and has_latin


def classify(preference, model_a, model_b):
    """Return (vote, tie_kind) for one raw preference_model value."""
    if preference == model_a:
        return "A", None
    if preference == model_b:
        return "B", None
    if preference == "Tie / No Preference":
        return "TIE", "no_preference"
    names = []
    for name in preference.split(","):
        names.append(name.strip())
    if sorted(names) == sorted([model_a, model_b]):
        return "TIE", "both_good"
    raise ValueError(f"unrecognised preference_model {preference!r} for {model_a!r} vs {model_b!r}")


def axes_json(fine_grained, key):
    """The axis ratings of one clip as JSON text, or None when they are missing."""
    if not isinstance(fine_grained, dict):
        return None
    ratings = fine_grained.get(key)
    if not ratings:
        return None
    return json.dumps(ratings, sort_keys=True)


def make_pair_id(row):
    """A stable id from the prompt and the two systems (the same for every vote on the pair)."""
    key = f"{row['academic_prompt_id']}|{row['model_a']}|{row['model_b']}"
    return "speecharena:" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def convert(rows):
    """Turn vote rows (dicts with COLUMNS) into (pairs, votes), two lists of dicts."""
    # pair_id -> first source row, its source_row text, and the list of votes (in order of first appearance)
    items = {}
    votes = []
    for row in rows:
        pair_id = make_pair_id(row)
        vote, tie_kind = classify(row["preference_model"], row["model_a"], row["model_b"])
        source_row = f"{row['src_shard']}:{row['src_row']}"
        if pair_id not in items:
            items[pair_id] = {"first": row, "source_row": source_row, "votes": []}
        item = items[pair_id]
        item["votes"].append(vote)
        fine_grained = row.get("fine_grained_eval")
        votes.append({
            "vote_id": f"{pair_id}:{len(item['votes']) - 1}",
            "pair_id": pair_id,
            "dataset": "speecharena",
            "rater_id": str(row["user_id"]),
            "rater_gender": row.get("gender"),
            "vote": vote,
            "strength": 0,
            "tie_kind": tie_kind,
            "axes_a": axes_json(fine_grained, "detailed_ratings_a"),
            "axes_b": axes_json(fine_grained, "detailed_ratings_b"),
            "source_row": source_row,
        })

    pairs = []
    for pair_id, item in items.items():
        first = item["first"]
        count_a = item["votes"].count("A")
        count_b = item["votes"].count("B")
        if count_a > count_b:
            label = "A"
        elif count_b > count_a:
            label = "B"
        else:
            label = "TIE"
        decided = count_a + count_b
        agreement = None
        if label != "TIE" and decided > 0:
            agreement = max(count_a, count_b) / decided
        mixed = is_mixed(first["sentence"])
        if mixed:
            lang = "hi-en"
        else:
            lang = "hi"
        pairs.append({
            "pair_id": pair_id,
            "dataset": "speecharena",
            "split": "unassigned",
            "source_split": None,
            "audio_a": f"speecharena_hi_AB:{item['source_row']}:A",
            "audio_b": f"speecharena_hi_AB:{item['source_row']}:B",
            "transcript": first["sentence"],
            "sentence_id": str(first["academic_prompt_id"]),
            "lang": lang,
            "mixed": mixed,
            "system_a": first["model_a"],
            "system_b": first["model_b"],
            "label": label,
            "strength": 0,
            "n_votes": len(item["votes"]),
            "n_decided": decided,
            "agreement": agreement,
            "source_row": item["source_row"],
        })
    return pairs, votes


def read_rows(root):
    """Read the text columns of every parquet file in root (the audio columns are never read)."""
    # imported here, so the other functions work (and are tested) without pyarrow installed
    import pyarrow.parquet
    rows = []
    for path in sorted(Path(root).glob("*.parquet")):
        # pyarrow (not pandas) keeps missing values as None and nested fields as dicts
        table = pyarrow.parquet.ParquetFile(path).read(columns=COLUMNS)
        rows.extend(table.to_pylist())
    return rows


def load(root):
    """Return (pairs, votes) for our filtered copy of SpeechArenaBench."""
    return convert(read_rows(root))
