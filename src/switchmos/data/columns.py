"""The columns of the three common tables, and checks for single rows.

RATINGS: one row per rating of a single clip (MOS or MUSHRA): SOMOS, BVCC, MANGO.
PAIRS:   one row per pair (same sentence, clip A vs clip B) with the final label: SpeechJudge, SpeechArenaBench.
VOTES:   one row per rater vote on a pair.

`split` is "unassigned" in these tables; make_splits.py assigns the real split later.
The dataset's own split name is kept in `source_split`.
Free-text comments of raters are not kept, because they may contain personal text.
"""

# column name: (type, required)
RATINGS_COLUMNS = {
    "rating_id": ("string", True),          # unique per row
    "dataset": ("string", True),            # somos | bvcc | mango
    "split": ("string", True),
    "source_split": ("string", False),      # the dataset's own split name, if any
    "clip_id": ("string", True),
    "audio_path": ("string", True),         # path inside the dataset folder, or "<zip>:<member>"
    "sr": ("int32", False),                 # sample rate in Hz
    "dur_s": ("float32", False),            # duration in seconds
    "transcript": ("string", False),
    "lang": ("string", True),               # hi | ta | en | zh | zh-en | hi-en
    "mixed": ("bool", False),               # code-switched sentence
    "system_id": ("string", True),          # TTS system, or natural / anchor / reference
    "rater_id": ("string", False),
    "rater_native": ("bool", False),        # SOMOS isNative
    "rater_reliability": ("float32", False),  # SOMOS listenerReliability
    "label_type": ("string", True),         # mos | mushra
    "score": ("float32", True),
    "score_min": ("float32", True),         # 1 for MOS, 0 for MUSHRA
    "score_max": ("float32", True),         # 5 for MOS, 100 for MUSHRA
    "page_id": ("string", False),           # listening-test page, to normalise within a page
    "variant": ("string", False),           # MANGO variant, e.g. mushra_dg_nmr
}

PAIRS_COLUMNS = {
    "pair_id": ("string", True),
    "dataset": ("string", True),            # speechjudge | speecharena
    "split": ("string", True),
    "source_split": ("string", False),
    "audio_a": ("string", True),            # reference to clip A
    "audio_b": ("string", True),            # reference to clip B
    "transcript": ("string", False),
    "sentence_id": ("string", False),       # groups pairs with the same text
    "lang": ("string", True),
    "mixed": ("bool", False),
    "system_a": ("string", False),          # empty when the dataset does not name the systems
    "system_b": ("string", False),
    "label": ("string", True),              # A | B | TIE
    "strength": ("int8", False),            # 0 unknown or tie, 1 slight, 2 strong
    "n_votes": ("int32", False),
    "n_decided": ("int32", False),          # votes that picked A or B
    "agreement": ("float32", False),        # share of decided votes that agree with the label
    "source_row": ("string", False),        # where the row came from, for tracing
}

VOTES_COLUMNS = {
    "vote_id": ("string", True),
    "pair_id": ("string", True),
    "dataset": ("string", True),
    "rater_id": ("string", False),
    "rater_gender": ("string", False),
    "vote": ("string", True),               # A | B | TIE
    "strength": ("int8", False),
    "tie_kind": ("string", False),          # both_good | both_bad | missing_reason | no_preference
    "axes_a": ("string", False),            # JSON of the six 1-5 axis ratings for clip A
    "axes_b": ("string", False),
    "source_row": ("string", False),
}

LABEL_TYPES = ["mos", "mushra"]
PAIR_LABELS = ["A", "B", "TIE"]
TIE_KINDS = ["both_good", "both_bad", "missing_reason", "no_preference"]
SPLITS = ["unassigned", "train", "val", "test", "test_extra", "unused"]
SCALES = {"mos": (1.0, 5.0), "mushra": (0.0, 100.0)}


def check_columns(row, columns, table_name):
    """Problems with missing required values or unknown column names."""
    errors = []
    for column in columns:
        required = columns[column][1]
        if required and row.get(column) in (None, ""):
            errors.append(f"{table_name}: missing required '{column}'")
    for column in row:
        if column not in columns:
            errors.append(f"{table_name}: unknown column '{column}'")
    return errors


def validate_rating(row):
    """Return a list of problems with one rating row (an empty list means the row is fine)."""
    errors = check_columns(row, RATINGS_COLUMNS, "rating")
    if row.get("label_type") not in LABEL_TYPES:
        errors.append(f"rating: label_type must be one of {sorted(LABEL_TYPES)}")
    if row.get("split") not in SPLITS:
        errors.append(f"rating: split must be one of {sorted(SPLITS)}")
    low = row.get("score_min")
    high = row.get("score_max")
    score = row.get("score")
    if low is not None and high is not None and score is not None:
        if not (low <= score <= high):
            errors.append(f"rating: score {score} outside [{low}, {high}]")
        expected = SCALES.get(row.get("label_type"))
        if expected is not None and (low, high) != expected:
            errors.append(f"rating: scale {(low, high)} does not match {row.get('label_type')} {expected}")
    return errors


def validate_pair(row):
    """Return a list of problems with one pair row."""
    errors = check_columns(row, PAIRS_COLUMNS, "pair")
    if row.get("label") not in PAIR_LABELS:
        errors.append(f"pair: label must be one of {sorted(PAIR_LABELS)}")
    if row.get("split") not in SPLITS:
        errors.append(f"pair: split must be one of {sorted(SPLITS)}")
    if row.get("strength") not in (None, 0, 1, 2):
        errors.append("pair: strength must be 0, 1, 2 or null")
    if row.get("audio_a") and row.get("audio_a") == row.get("audio_b"):
        errors.append("pair: audio_a and audio_b are identical")
    n_votes = row.get("n_votes")
    n_decided = row.get("n_decided")
    if n_votes is not None and n_decided is not None and n_decided > n_votes:
        errors.append("pair: n_decided cannot exceed n_votes")
    return errors


def validate_vote(row):
    """Return a list of problems with one vote row."""
    errors = check_columns(row, VOTES_COLUMNS, "vote")
    if row.get("vote") not in PAIR_LABELS:
        errors.append(f"vote: vote must be one of {sorted(PAIR_LABELS)}")
    tie_kind = row.get("tie_kind")
    if tie_kind is not None and tie_kind not in TIE_KINDS:
        errors.append(f"vote: tie_kind must be one of {sorted(TIE_KINDS)} or null")
    if row.get("vote") != "TIE" and tie_kind is not None:
        errors.append("vote: tie_kind only allowed on TIE votes")
    return errors
