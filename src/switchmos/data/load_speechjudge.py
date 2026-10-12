"""SpeechJudge-Data loader: pairs with 2-3 rater votes each.

A vote is "A+1", "A+2", "B+1", "B+2" (the +1/+2 is the strength), or one of three tie texts.
The pair label is the dataset's majority label. System names are not released.
"""
import hashlib
from pathlib import Path

COLUMNS = ["index", "subset", "language_setting", "chosen", "target_text", "rater", "naturalness_annotation", "naturalness_label"]
VOTES = {"A+1": ("A", 1), "A+2": ("A", 2), "B+1": ("B", 1), "B+2": ("B", 2)}
TIE_KINDS = {"Tie (both very good)": "both_good", "Tie (both not good)": "both_bad", "Tie (missing reason)": "missing_reason"}
LABELS = {"A": "A", "B": "B", "Tie": "TIE"}


def parse_vote(text):
    """Return (side, strength, tie_kind) for one raw vote text."""
    if text in VOTES:
        side, strength = VOTES[text]
        return side, strength, None
    if text in TIE_KINDS:
        return "TIE", 0, TIE_KINDS[text]
    raise ValueError(f"unknown SpeechJudge vote: {text!r}")


def sentence_id(text):
    """A short id of the sentence text, so pairs with the same text can be grouped."""
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:12]


def language(setting):
    """'en2zh' -> ('zh', False); 'zh2mixed' -> ('zh-en', True): the target language and whether it is code-switched."""
    target = setting.split("2")[-1]
    if target == "mixed":
        return "zh-en", True
    return target, False


def convert(row, source_split):
    """Turn one source row into (pair_row, list_of_vote_rows)."""
    votes = []
    for text in row["naturalness_annotation"]:
        votes.append(parse_vote(text))
    raters = list(row["rater"])
    if len(votes) != len(raters):
        raise ValueError(f"index {row['index']}: {len(votes)} votes but {len(raters)} raters")

    label = LABELS[row["naturalness_label"]]
    pair_id = f"speechjudge:{row['index']}"
    lang, mixed = language(row["language_setting"])
    n_decided = 0
    winning_strengths = []
    for side, strength, tie_kind in votes:
        if side in ("A", "B"):
            n_decided += 1
        if label != "TIE" and side == label:
            winning_strengths.append(strength)
    strength = 0
    if winning_strengths:
        # mean strength of the winning votes, rounded half up (1.5 -> 2)
        strength = int(sum(winning_strengths) / len(winning_strengths) + 0.5)
    agreement = None
    if label != "TIE" and n_decided > 0:
        agreement = len(winning_strengths) / n_decided
    source_row = f"{source_split}:{row['index']}"

    pair = {
        "pair_id": pair_id,
        "dataset": "speechjudge",
        "split": "unassigned",
        "source_split": source_split,
        "audio_a": f"{pair_id}:A",
        "audio_b": f"{pair_id}:B",
        "transcript": row.get("target_text"),
        "sentence_id": sentence_id(row.get("target_text")),
        "lang": lang,
        "mixed": mixed,
        "system_a": None,
        "system_b": None,
        "label": label,
        "strength": strength,
        "n_votes": len(votes),
        "n_decided": n_decided,
        "agreement": agreement,
        "source_row": source_row,
    }
    vote_rows = []
    for i in range(len(votes)):
        side, vote_strength, tie_kind = votes[i]
        vote_rows.append({
            "vote_id": f"{pair_id}:{i}",
            "pair_id": pair_id,
            "dataset": "speechjudge",
            "rater_id": str(raters[i]),
            "rater_gender": None,
            "vote": side,
            "strength": vote_strength,
            "tie_kind": tie_kind,
            "axes_a": None,
            "axes_b": None,
            "source_row": source_row,
        })
    return pair, vote_rows


def read_rows(root):
    """Return (source_split, row) for every row of every parquet file under root (text columns only)."""
    # imported here, so the other functions work (and are tested) without pyarrow installed
    import pyarrow.parquet
    rows = []
    for path in sorted(Path(root).rglob("*.parquet")):
        split = path.name.split("-")[0]          # file names start with train | dev | test | other
        # pyarrow (not pandas) keeps missing values as None and lists as Python lists
        table = pyarrow.parquet.ParquetFile(path).read(columns=COLUMNS)
        for row in table.to_pylist():
            rows.append((split, row))
    return rows


def load(root):
    """Return (pairs, votes) as two lists of dicts."""
    pairs = []
    votes = []
    for split, row in read_rows(root):
        pair, vote_rows = convert(row, split)
        pairs.append(pair)
        votes.extend(vote_rows)
    pair_ids = set()
    for pair in pairs:
        pair_ids.add(pair["pair_id"])
    if len(pair_ids) != len(pairs):
        raise ValueError("SpeechJudge index is not unique across splits")
    return pairs, votes
