import unittest

from switchmos.data import make_splits

FOLDERS = {"ta": "Tamil", "hi": "Hindi", "en": "English"}
NAMES = [f"stim_{i}.wav" for i in range(100)]


def mango_row(lang, name, system="FS2"):
    """A made-up MANGO row with only the columns the split code reads."""
    return {"lang": lang, "audio_path": f"audios/{FOLDERS[lang]}/{system}/{name}"}


def mango_assignments():
    """Assignments for 100 Tamil and 100 Hindi sentences."""
    rows = []
    for lang in ["ta", "hi"]:
        for name in NAMES:
            rows.append(mango_row(lang, name))
    return make_splits.mango_assignments(rows)


def tamil_splits(version, assignments):
    """The split of every Tamil sentence, in NAMES order."""
    splits = []
    for name in NAMES:
        splits.append(make_splits.mango_split(mango_row("ta", name), version, assignments))
    return splits


class TestSplits(unittest.TestCase):
    def test_rank_buckets_exact_and_order_independent(self):
        keys = [f"k{i}" for i in range(100)]
        buckets = make_splits.rank_buckets(keys)
        values = list(buckets.values())
        self.assertEqual(values.count("test"), 10)
        self.assertEqual(values.count("val"), 10)
        self.assertEqual(values.count("train"), 80)
        self.assertEqual(buckets, make_splits.rank_buckets(list(reversed(keys))))
        small = list(make_splits.rank_buckets([f"e{i}" for i in range(30)]).values())
        self.assertEqual(small.count("test"), 3)
        self.assertEqual(small.count("val"), 3)

    def test_same_sentence_same_split_for_every_system(self):
        assignments = mango_assignments()
        for version in make_splits.VERSIONS:
            splits = set()
            for system in ["FS2", "VITS", "REF", "ANC"]:
                splits.add(make_splits.mango_split(mango_row("ta", "stim_7.wav", system), version, assignments))
            self.assertEqual(len(splits), 1)

    def test_tamil_versions_share_the_same_test_sentences(self):
        assignments = mango_assignments()
        out_splits = tamil_splits("tamil_out", assignments)
        in_splits = tamil_splits("tamil_in", assignments)
        out_test = set()
        in_test = set()
        for i in range(len(NAMES)):
            if out_splits[i] == "test":
                out_test.add(NAMES[i])
            if in_splits[i] == "test":
                in_test.add(NAMES[i])
        self.assertEqual(out_test, in_test)
        self.assertEqual(len(out_test), 10)

    def test_tamil_out_keeps_tamil_out_of_training(self):
        assignments = mango_assignments()
        out_splits = tamil_splits("tamil_out", assignments)
        self.assertEqual(out_splits.count("test"), 10)
        self.assertEqual(out_splits.count("test_extra"), 90)
        in_splits = tamil_splits("tamil_in", assignments)
        self.assertEqual(in_splits.count("train"), 80)
        self.assertEqual(in_splits.count("val"), 10)
        self.assertEqual(in_splits.count("test"), 10)

    def test_hindi_is_split_the_same_way_in_both_versions(self):
        assignments = mango_assignments()
        for name in NAMES:
            row = mango_row("hi", name)
            self.assertEqual(make_splits.mango_split(row, "tamil_out", assignments),
                             make_splits.mango_split(row, "tamil_in", assignments))

    def test_official_mappings(self):
        version = "tamil_out"
        expected = {"train": "train", "dev": "val", "test": "test", "other": "unused"}
        for source_split in expected:
            got = make_splits.split_for("speechjudge", {"source_split": source_split}, version)
            self.assertEqual(got, expected[source_split])
        expected = {"train": "train", "valid": "val", "test": "test"}
        for source_split in expected:
            got = make_splits.split_for("somos", {"source_split": source_split}, version)
            self.assertEqual(got, expected[source_split])
        self.assertEqual(make_splits.split_for("bvcc", {"source_split": "dev"}, version), "val")
        self.assertEqual(make_splits.split_for("speecharena", {}, version), "test")

    def test_unknown_inputs_raise(self):
        with self.assertRaises(ValueError):
            make_splits.split_for("somos", {"source_split": "train"}, "tamil_maybe")
        with self.assertRaises(KeyError):
            make_splits.split_for("somos", {"source_split": "dev"}, "tamil_in")      # SOMOS spells it valid

    def test_every_rule_produces_a_known_split_name(self):
        produced = ["test", "test_extra", "train", "val"]
        for mapping in make_splits.OFFICIAL.values():
            produced.extend(mapping.values())
        for split in produced:
            self.assertIn(split, make_splits.SPLIT_NAMES)


if __name__ == "__main__":
    unittest.main()
