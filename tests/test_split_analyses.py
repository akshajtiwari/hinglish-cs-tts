"""Checks for the system-vs-clip split scripts: paper_a_extra_analyses, make_pair_tables and within_system."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

# these scripts import their neighbours by plain name, as they do when run from the command line
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "step2_baselines"))
import make_pair_tables
import script_subsets

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
if HAS_NUMPY:
    import paper_a_extra_analyses as extra
    import within_system


def vote(number, sentence, system_a, system_b, label, judge_a, judge_b, rater="r"):
    """One decided vote, already joined with one judge's scores (as join_scores would leave it)."""
    winner = system_a if label == "A" else system_b
    row = {"vote_id": str(number), "pair_id": sentence + system_a + system_b, "sentence_id": sentence,
           "system_a": system_a, "system_b": system_b, "label": label, "winner": winner, "mixed": False,
           "rater_id": rater, "pairing": " vs ".join(sorted([system_a, system_b])),
           "judge_a": judge_a, "judge_b": judge_b, "judge_credit": 0.5}
    if judge_a != judge_b:
        row["judge_credit"] = float((judge_a > judge_b) == (label == "A"))
    return row


@unittest.skipUnless(HAS_NUMPY, "needs numpy")
class TestSplitRunner(unittest.TestCase):
    def test_system_only_judge_has_half_balanced_accuracy(self):
        # X wins 8 of 10 votes; the judge always scores X higher, so it is right exactly when X wins
        rows = []
        for i in range(10):
            label = "A" if i < 8 else "B"
            rows.append(vote(i, "s" + str(i), "X", "Y", label, 2.0, 1.0))
        report = extra.analyse(rows, ["judge"], ["judge"], "")
        block = report["subsets"]["all"]
        self.assertAlmostEqual(block["stronger_system"], 0.8)
        self.assertAlmostEqual(block["rules"]["judge"]["accuracy"], 0.8)
        self.assertAlmostEqual(block["rules"]["judge"]["winner_balanced"], 0.5)
        self.assertAlmostEqual(block["rules"]["judge"]["minus_stronger_system"], 0.0)
        # a constant preference gives every won vote the same difference as every lost one: AUC 0.5
        self.assertAlmostEqual(block["rules"]["judge"]["auc"], 0.5)
        self.assertIsNone(report["rater_reference"])
        self.assertEqual(len(report["holm_family"]), 3)

    def test_clip_judge_beats_the_system_rule(self):
        # the judge follows the clips: right on every vote, so balanced accuracy and AUC are 1
        rows = []
        for i in range(10):
            label = "A" if i < 7 else "B"
            if label == "A":
                rows.append(vote(i, "s" + str(i), "X", "Y", label, 3.0, 1.0))
            else:
                rows.append(vote(i, "s" + str(i), "X", "Y", label, 1.0, 3.0))
        block = extra.analyse(rows, ["judge"], ["judge"], "")["subsets"]["all"]
        self.assertAlmostEqual(block["rules"]["judge"]["winner_balanced"], 1.0)
        self.assertAlmostEqual(block["rules"]["judge"]["auc"], 1.0)
        self.assertAlmostEqual(block["rules"]["judge"]["minus_stronger_system"], 0.3)

    def test_judge_minus_feature_rule_is_paired(self):
        # the judge follows the clips, the feature rule always picks clip A: the difference is judge minus rule
        rows = []
        for i in range(10):
            label = "A" if i < 7 else "B"
            row = vote(i, "s" + str(i), "X", "Y", label, 3.0, 1.0) if label == "A" else vote(i, "s" + str(i), "X", "Y", label, 1.0, 3.0)
            row["first_a"] = 1.0
            row["first_b"] = 0.0
            row["first_credit"] = float(label == "A")
            rows.append(row)
        report = extra.analyse(rows, ["judge"], ["judge", "first"], "")
        block = report["judge_minus_feature_rule"]["judge minus first"]
        point = report["subsets"]["all"]["rules"]
        self.assertAlmostEqual(block["winner_balanced"], point["judge"]["winner_balanced"] - point["first"]["winner_balanced"])
        self.assertAlmostEqual(block["winner_balanced"], 0.5)
        self.assertLessEqual(block["winner_balanced_ci95"][0], block["winner_balanced"])
        self.assertEqual(len(report["holm_family"]), 3)

    def test_stronger_system_rule_uses_draw_weights(self):
        rows = [vote(0, "a", "X", "Y", "A", 1.0, 0.0), vote(1, "b", "X", "Y", "B", 1.0, 0.0),
                vote(2, "c", "X", "Y", "B", 1.0, 0.0)]
        index = {"a": 0, "b": 1, "c": 2}
        arrays = extra.VoteArrays(rows, index, ["judge"])
        self.assertAlmostEqual(arrays.stronger_system(extra.numpy.array([1.0, 1.0, 1.0])), 2 / 3)
        # drawing sentence a three times makes X the stronger system: 3 of 4 weighted votes
        self.assertAlmostEqual(arrays.stronger_system(extra.numpy.array([3.0, 1.0, 0.0])), 3 / 4)
        self.assertIsNone(arrays.accuracy("judge", extra.numpy.array([0.0, 0.0, 0.0])))

    def test_rater_reference_needs_two_raters(self):
        one = vote(0, "a", "X", "Y", "A", 1.0, 0.0, rater="r1")
        two = vote(1, "a", "X", "Y", "A", 1.0, 0.0, rater="r2")
        self.assertEqual(extra.rater_reference([one]), [])
        self.assertEqual(len(extra.rater_reference([one, two])), 2)
        self.assertEqual(extra.rater_measures([], extra.numpy.ones(1), {"a": 0}), (None, None))

    def test_feature_rule_credit(self):
        rows = [{"path_a": "p", "path_b": "q", "label": "A"}, {"path_a": "q", "path_b": "p", "label": "A"},
                {"path_a": "p", "path_b": "p", "label": "B"}]
        with tempfile.TemporaryDirectory() as folder:
            features = Path(folder) / "features.csv"
            features.write_text("path,rms\np,2.0\nq,1.0\n")
            extra.add_feature_rule(rows, features, "rms", "louder_clip")
        self.assertEqual([row["louder_clip_credit"] for row in rows], [1.0, 0.0, 0.5])
        self.assertEqual(rows[1]["louder_clip_a"], 1.0)
        self.assertEqual(extra.parse_feature_rules("seconds:longer_clip,rms:louder_clip"),
                         [("seconds", "longer_clip"), ("rms", "louder_clip")])

    def test_holm(self):
        self.assertEqual(extra.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

    def test_empty_subset_raises(self):
        rows = [vote(0, "a", "X", "Y", "A", 1.0, 0.0), vote(1, "b", "X", "Y", "B", 1.0, 0.0)]
        with self.assertRaises(ValueError):
            extra.analyse(rows, ["judge"], ["judge"], "mixed")


@unittest.skipUnless(HAS_NUMPY, "needs numpy")
class TestWithinSystem(unittest.TestCase):
    def clips(self):
        rows = []
        # system good: high MOS; judge follows MOS inside the system. system bad: judge is constant (skipped)
        for i, mos in enumerate([4.0, 4.2, 4.4, 4.6]):
            rows.append({"clip_id": f"S{i}_good", "system": "good", "mos": mos, "judge": mos})
        for i, mos in enumerate([2.0, 2.2, 2.4, 2.6]):
            rows.append({"clip_id": f"S{i}_bad", "system": "bad", "mos": mos, "judge": 1.0})
        return rows

    def test_leave_one_out_and_within_system(self):
        clips = self.clips()
        within_system.add_leave_one_out_means(clips)
        self.assertAlmostEqual(clips[0]["system_rule"], (4.2 + 4.4 + 4.6) / 3)
        values = within_system.within_system_values(clips, "judge")
        self.assertEqual(list(values), ["good"])
        self.assertAlmostEqual(values["good"], 1.0)

    def test_same_sentence_pairs(self):
        clips = self.clips()
        within_system.add_leave_one_out_means(clips)
        pairs = within_system.same_sentence_pairs(clips, ["judge"], 0.5)
        # four sentences, each with one good and one bad clip, MOS gap 2.0
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            self.assertEqual(pair["system_rule"], 1.0)
            self.assertEqual(pair["judge"], 1.0)
        self.assertEqual(within_system.same_sentence_pairs(clips, ["judge"], 3.0), [])


class TestScriptSubsets(unittest.TestCase):
    def test_latin_only_sentences_are_kept_apart(self):
        votes = [{"sentence_id": "d", "label": "A"}, {"sentence_id": "m", "label": "B"}, {"sentence_id": "l", "label": "A"}]
        transcripts = {"d": "यह है", "m": "यह test है", "l": "Clock mein baje"}
        classes = script_subsets.split_votes(votes, transcripts)
        self.assertEqual([len(classes[k]) for k in ["native", "mixed", "latin"]], [1, 1, 1])
        self.assertEqual(classes["mixed"][0]["mixed_script"], "True")
        self.assertEqual(classes["native"][0]["mixed_script"], "False")


class TestMangoPages(unittest.TestCase):
    def test_page_pairs(self):
        clips = []
        for system, mos in [("FS2", "60"), ("VITS", "70"), ("anchor", "20"), ("reference", "70")]:
            clips.append({"lang": "ta", "variant": "mushra", "system": system, "mos": mos, "path": "/a/" + system,
                          "audio_path": f"audios/Tamil/{system}/s1.wav", "audio_status": "ok"})
        rows, equal = make_pair_tables.page_pairs(clips, "ta", "mushra", [])
        self.assertEqual(len(rows), 5)
        self.assertEqual(equal, 1)
        for row in rows:
            self.assertEqual(list(row), make_pair_tables.COLUMNS)
            self.assertEqual(row["sentence_id"], "s1.wav")
        rows, equal = make_pair_tables.page_pairs(clips, "ta", "mushra", ["anchor", "reference"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["label"], "B")


if __name__ == "__main__":
    unittest.main()
