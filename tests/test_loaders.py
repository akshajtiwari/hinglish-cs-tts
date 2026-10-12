"""Loader tests on tiny made-up rows (no pyarrow, no files needed)."""
import io
import json
import unittest

from switchmos.data import columns
from switchmos.data import load_bvcc
from switchmos.data import load_mango
from switchmos.data import load_somos
from switchmos.data import load_speecharena
from switchmos.data import load_speechjudge


class TestSpeechJudge(unittest.TestCase):
    def test_parse_vote(self):
        self.assertEqual(load_speechjudge.parse_vote("A+2"), ("A", 2, None))
        self.assertEqual(load_speechjudge.parse_vote("B+1"), ("B", 1, None))
        self.assertEqual(load_speechjudge.parse_vote("Tie (both very good)"), ("TIE", 0, "both_good"))
        self.assertEqual(load_speechjudge.parse_vote("Tie (both not good)"), ("TIE", 0, "both_bad"))
        self.assertEqual(load_speechjudge.parse_vote("Tie (missing reason)"), ("TIE", 0, "missing_reason"))
        with self.assertRaises(ValueError):
            load_speechjudge.parse_vote("C+1")

    def test_language(self):
        self.assertEqual(load_speechjudge.language("en2zh"), ("zh", False))
        self.assertEqual(load_speechjudge.language("en2en"), ("en", False))
        self.assertEqual(load_speechjudge.language("zh2mixed"), ("zh-en", True))

    def test_convert_decided_pair(self):
        row = {"index": 7, "language_setting": "zh2mixed", "target_text": "hello", "rater": ["r1", "r2", "r3"],
               "naturalness_annotation": ["A+2", "A+1", "B+1"], "naturalness_label": "A"}
        pair, votes = load_speechjudge.convert(row, "train")
        self.assertEqual(pair["label"], "A")
        self.assertEqual(pair["n_votes"], 3)
        self.assertEqual(pair["n_decided"], 3)
        self.assertAlmostEqual(pair["agreement"], 2 / 3)
        self.assertEqual(pair["strength"], 2)           # mean of the winning strengths, 1.5, rounds up
        self.assertEqual(pair["lang"], "zh-en")
        self.assertEqual(pair["mixed"], True)
        self.assertEqual(pair["source_split"], "train")
        self.assertEqual(pair["split"], "unassigned")
        self.assertEqual([vote["vote"] for vote in votes], ["A", "A", "B"])
        self.assertEqual(columns.validate_pair(pair), [])
        for vote in votes:
            self.assertEqual(columns.validate_vote(vote), [])

    def test_convert_tie_pair(self):
        row = {"index": 8, "language_setting": "en2en", "target_text": "x", "rater": ["r1", "r2"],
               "naturalness_annotation": ["Tie (both very good)", "Tie (both not good)"], "naturalness_label": "Tie"}
        pair, votes = load_speechjudge.convert(row, "other")
        self.assertEqual(pair["label"], "TIE")
        self.assertEqual(pair["strength"], 0)
        self.assertEqual(pair["n_decided"], 0)
        self.assertIsNone(pair["agreement"])
        self.assertEqual([vote["tie_kind"] for vote in votes], ["both_good", "both_bad"])
        self.assertEqual(columns.validate_pair(pair), [])

    def test_rater_count_mismatch_raises(self):
        row = {"index": 9, "language_setting": "en2en", "target_text": "x", "rater": ["r1"],
               "naturalness_annotation": ["A+1", "B+1"], "naturalness_label": "A"}
        with self.assertRaises(ValueError):
            load_speechjudge.convert(row, "train")


def arena_row(preference, prompt="p1", user="u1", n=0, fine_grained=None):
    """One made-up SpeechArenaBench vote row."""
    if fine_grained is None:
        fine_grained = {
            "additional_comment": "SECRET FREE TEXT",
            "detailed_ratings_a": {"noise": 5, "liveliness": 4},
            "detailed_ratings_b": {"noise": 2, "liveliness": 1},
        }
    return {
        "academic_prompt_id": prompt,
        "sentence": "यह एक test है",
        "model_a": "Gemini 2.5 Pro TTS",
        "model_b": "Sonic 3",
        "user_id": user,
        "gender": "male",
        "preference_model": preference,
        "fine_grained_eval": fine_grained,
        "src_shard": "val-00000-of-00070.parquet",
        "src_row": n,
    }


class TestSpeechArena(unittest.TestCase):
    def test_classify(self):
        a = "Gemini 2.5 Pro TTS"
        b = "Sonic 3"
        self.assertEqual(load_speecharena.classify(a, a, b), ("A", None))
        self.assertEqual(load_speecharena.classify(b, a, b), ("B", None))
        self.assertEqual(load_speecharena.classify("Tie / No Preference", a, b), ("TIE", "no_preference"))
        self.assertEqual(load_speecharena.classify("Gemini 2.5 Pro TTS, Sonic 3", a, b), ("TIE", "both_good"))
        self.assertEqual(load_speecharena.classify("Sonic 3, Gemini 2.5 Pro TTS", a, b), ("TIE", "both_good"))
        with self.assertRaises(ValueError):
            load_speecharena.classify("GPT 4o Mini TTS, Sonic 3", a, b)

    def test_is_mixed(self):
        self.assertTrue(load_speecharena.is_mixed("यह एक test है"))
        self.assertFalse(load_speecharena.is_mixed("यह है"))
        self.assertFalse(load_speecharena.is_mixed("only latin"))

    def test_convert_votes_into_pair(self):
        rows = [
            arena_row("Gemini 2.5 Pro TTS", user="u1", n=0),
            arena_row("Gemini 2.5 Pro TTS", user="u2", n=1),
            arena_row("Gemini 2.5 Pro TTS, Sonic 3", user="u3", n=2),
        ]
        pairs, votes = load_speecharena.convert(rows)
        self.assertEqual(len(pairs), 1)
        pair = pairs[0]
        self.assertEqual(pair["label"], "A")
        self.assertEqual(pair["n_votes"], 3)
        self.assertEqual(pair["n_decided"], 2)
        self.assertEqual(pair["agreement"], 1.0)
        self.assertEqual(pair["lang"], "hi-en")
        self.assertEqual(pair["mixed"], True)
        self.assertEqual(pair["system_a"], "Gemini 2.5 Pro TTS")
        self.assertEqual(pair["system_b"], "Sonic 3")
        self.assertEqual([vote["vote"] for vote in votes], ["A", "A", "TIE"])
        self.assertEqual(votes[2]["tie_kind"], "both_good")
        self.assertEqual(json.loads(votes[0]["axes_a"]), {"liveliness": 4, "noise": 5})
        self.assertEqual(columns.validate_pair(pair), [])
        for vote in votes:
            self.assertEqual(columns.validate_vote(vote), [])

    def test_comments_are_dropped(self):
        pairs, votes = load_speecharena.convert([arena_row("Sonic 3")])
        self.assertNotIn("SECRET", json.dumps(pairs) + json.dumps(votes))

    def test_split_votes_give_tie_and_distinct_items(self):
        rows = [
            arena_row("Gemini 2.5 Pro TTS", user="u1", n=0),
            arena_row("Sonic 3", user="u2", n=1),
            arena_row("Tie / No Preference", prompt="p2", user="u3", n=2),
        ]
        pairs, votes = load_speecharena.convert(rows)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0]["label"], "TIE")          # one A vote and one B vote
        self.assertIsNone(pairs[0]["agreement"])
        self.assertEqual(pairs[1]["label"], "TIE")
        self.assertEqual(pairs[1]["n_decided"], 0)
        self.assertNotEqual(pairs[0]["pair_id"], pairs[1]["pair_id"])

    def test_missing_fine_grained_is_allowed(self):
        pairs, votes = load_speecharena.convert([arena_row("Sonic 3", fine_grained={})])
        self.assertIsNone(votes[0]["axes_a"])


class TestMango(unittest.TestCase):
    def test_name_parts(self):
        self.assertEqual(load_mango.name_parts("tamil_mushra_dg_nmr.csv"), ("ta", "mushra_dg_nmr", "tamil_mushra_dg_nmr"))
        self.assertEqual(load_mango.name_parts("hindi_extended.csv")[:2], ("hi", "extended"))

    def test_convert_rows(self):
        page = {"Rater_ID": "431", "FS2_Score": "80", "VITS_Score": "70", "ST2_Score": "80", "ANC_Score": "25", "REF_Score": "60",
                "FS2_Audio": "audios/Tamil/FS2/a.wav", "VITS_Audio": "audios/Tamil/VITS/a.wav", "ST2_Audio": "audios/Tamil/ST2/a.wav",
                "ANC_Audio": "audios/Tamil/ANC/a.wav", "REF_Audio": "audios/Tamil/REF/a.wav"}
        second_page = dict(page)
        second_page["Rater_ID"] = "432"
        rows = load_mango.convert_rows("tamil_mushra_dg_nmr.csv", [page, second_page])
        self.assertEqual(len(rows), 10)                      # 2 pages x 5 systems
        anchor = None
        systems = set()
        pages = set()
        for row in rows:
            systems.add(row["system_id"])
            pages.add(row["page_id"])
            if row["system_id"] == "anchor" and anchor is None:
                anchor = row
            self.assertEqual(columns.validate_rating(row), [])
        self.assertEqual(anchor["score"], 25.0)
        self.assertEqual(anchor["score_min"], 0.0)
        self.assertEqual(anchor["score_max"], 100.0)
        self.assertEqual(anchor["lang"], "ta")
        self.assertEqual(anchor["variant"], "mushra_dg_nmr")
        self.assertEqual(systems, {"FS2", "VITS", "ST2", "anchor", "reference"})
        self.assertEqual(len(pages), 2)

    def test_extended_has_seven_systems_and_empty_scores_are_skipped(self):
        page = {"Rater_ID": "1"}
        for system in load_mango.SYSTEMS:
            page[f"{system}_Score"] = "50"
            page[f"{system}_Audio"] = f"audios/Hindi/{system}/a.wav"
        self.assertEqual(len(load_mango.convert_rows("hindi_extended.csv", [page])), 7)
        page["XTTS_Score"] = ""
        self.assertEqual(len(load_mango.convert_rows("hindi_extended.csv", [page])), 6)


class TestSomos(unittest.TestCase):
    TSV = ("utteranceId\tchoice\tsentenceId\tsystemId\tmodelId\ttestpageId\tlocale\tlistenerId\tisNative\twrongValidation\tlowNatural\t"
           "sameScores\thighSynthetic\tclean\tlistenerReliability\n"
           "novel_2007_0098_015\t4\tnovel_2007_0098\t015\tm1\t000\tgb\tKEXM49572020611127\t1\t1\t1\t1\t1\t1\t1.0\n"
           "gt_LJ017-0230_000\t5\tLJ017-0230\t000\tm0\t000\tgb\tONJP34545176526892\t0\t1\t1\t1\t1\t1\t0.5\n")

    def test_convert_lines(self):
        rows = load_somos.convert_lines(io.StringIO(self.TSV), "train")
        self.assertEqual(len(rows), 2)
        first = rows[0]
        second = rows[1]
        self.assertEqual(first["score"], 4.0)
        self.assertEqual(first["score_min"], 1.0)
        self.assertEqual(first["score_max"], 5.0)
        self.assertEqual(first["label_type"], "mos")
        self.assertEqual(first["rater_id"], "KEXM49572020611127")
        self.assertEqual(first["rater_native"], True)
        self.assertEqual(first["rater_reliability"], 1.0)
        self.assertEqual(second["rater_native"], False)
        self.assertEqual(second["rater_reliability"], 0.5)
        self.assertEqual(second["source_split"], "train")
        self.assertEqual(first["audio_path"], "audios.zip:novel_2007_0098_015.wav")
        for row in rows:
            self.assertEqual(columns.validate_rating(row), [])


class TestBvcc(unittest.TestCase):
    def test_convert_lines(self):
        lines = ["sys4bafa,utt1.wav,4,ignore,{}_30-39_LISTENER42_F_x_y_none\n", "\n"]
        rows = load_bvcc.convert_lines(lines, "test")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["score"], 4.0)
        self.assertEqual(row["system_id"], "sys4bafa")
        self.assertEqual(row["clip_id"], "utt1.wav")
        self.assertEqual(row["source_split"], "test")
        self.assertEqual(row["rater_id"], "LISTENER42")
        self.assertEqual(columns.validate_rating(row), [])

    def test_bad_line_raises(self):
        with self.assertRaises(ValueError):
            load_bvcc.convert_lines(["only,three,fields"], "train")


if __name__ == "__main__":
    unittest.main()
