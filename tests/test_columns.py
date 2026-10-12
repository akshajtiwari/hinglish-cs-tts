import unittest

from switchmos.data import columns


def good_rating(**changes):
    """A valid rating row, with some values changed."""
    row = {
        "rating_id": "mango:1",
        "dataset": "mango",
        "split": "unassigned",
        "clip_id": "c1",
        "audio_path": "audios/Hindi/VITS/a.wav",
        "lang": "hi",
        "system_id": "VITS",
        "label_type": "mushra",
        "score": 70.0,
        "score_min": 0.0,
        "score_max": 100.0,
    }
    row.update(changes)
    return row


def good_pair(**changes):
    """A valid pair row, with some values changed."""
    row = {"pair_id": "sj:1", "dataset": "speechjudge", "split": "unassigned", "audio_a": "a", "audio_b": "b",
           "lang": "en", "label": "A"}
    row.update(changes)
    return row


def good_vote(**changes):
    """A valid vote row, with some values changed."""
    row = {"vote_id": "sj:1:0", "pair_id": "sj:1", "dataset": "speechjudge", "vote": "A"}
    row.update(changes)
    return row


def any_error_mentions(errors, word):
    """True if one of the error texts contains the word."""
    for error in errors:
        if word in error:
            return True
    return False


class TestColumns(unittest.TestCase):
    def test_valid_rows_pass(self):
        self.assertEqual(columns.validate_rating(good_rating()), [])
        self.assertEqual(columns.validate_pair(good_pair()), [])
        self.assertEqual(columns.validate_vote(good_vote()), [])

    def test_missing_required_is_reported(self):
        row = good_rating()
        del row["system_id"]
        self.assertTrue(any_error_mentions(columns.validate_rating(row), "system_id"))

    def test_unknown_column_is_reported(self):
        self.assertTrue(any_error_mentions(columns.validate_pair(good_pair(surprise=1)), "surprise"))

    def test_rating_scale_checks(self):
        self.assertTrue(columns.validate_rating(good_rating(score=120.0)))          # outside 0-100
        self.assertTrue(columns.validate_rating(good_rating(label_type="mos")))     # 0-100 is not a MOS scale
        mos_row = good_rating(label_type="mos", score=3.0, score_min=1.0, score_max=5.0)
        self.assertEqual(columns.validate_rating(mos_row), [])

    def test_split_must_be_known(self):
        self.assertTrue(columns.validate_rating(good_rating(split="validation")))
        self.assertEqual(columns.validate_pair(good_pair(split="val")), [])
        self.assertTrue(columns.validate_pair(good_pair(split="dev")))             # the project says val, not dev

    def test_pair_checks(self):
        self.assertTrue(columns.validate_pair(good_pair(label="C")))
        self.assertTrue(columns.validate_pair(good_pair(strength=3)))
        self.assertTrue(columns.validate_pair(good_pair(audio_b="a")))               # identical clips
        self.assertTrue(columns.validate_pair(good_pair(n_votes=2, n_decided=3)))    # more decided votes than votes
        tie_pair = good_pair(label="TIE", strength=0, n_votes=2, n_decided=0)
        self.assertEqual(columns.validate_pair(tie_pair), [])

    def test_vote_checks(self):
        self.assertTrue(columns.validate_vote(good_vote(vote="X")))
        self.assertTrue(columns.validate_vote(good_vote(vote="TIE", tie_kind="because")))
        self.assertTrue(columns.validate_vote(good_vote(vote="A", tie_kind="both_good")))   # tie_kind only on TIE votes
        self.assertEqual(columns.validate_vote(good_vote(vote="TIE", tie_kind="both_good")), [])

    def test_every_column_has_a_known_type(self):
        known = ["string", "int32", "int8", "float32", "bool"]
        for table in [columns.RATINGS_COLUMNS, columns.PAIRS_COLUMNS, columns.VOTES_COLUMNS]:
            for name, (kind, required) in table.items():
                self.assertIn(kind, known, name)

    def test_no_free_text_comment_column(self):
        for table in [columns.RATINGS_COLUMNS, columns.PAIRS_COLUMNS, columns.VOTES_COLUMNS]:
            for name in table:
                self.assertNotIn("comment", name)


if __name__ == "__main__":
    unittest.main()
