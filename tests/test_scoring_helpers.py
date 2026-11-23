"""Checks for the seeded UTMOSv2 chunks (score_baselines) and the SpeechJudge UTMOS variant helpers."""
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "step2_baselines"))

HAS_TORCH = importlib.util.find_spec("torch") is not None
HAS_NUMPY = importlib.util.find_spec("numpy") is not None


@unittest.skipUnless(HAS_TORCH, "score_baselines needs torch")
class MakeChunksTest(unittest.TestCase):
    def test_resumed_seeded_run_meets_the_same_chunks(self):
        import score_baselines
        paths = [f"f{i}" for i in range(7)]
        fresh = score_baselines.make_chunks(paths, set(), 3, seed=2)
        self.assertEqual(fresh, [(0, ["f0", "f1", "f2"]), (1, ["f3", "f4", "f5"]), (2, ["f6"])])
        # chunk 0 saved before a shutdown: the rest keep their numbers (and so their seeds)
        resumed = score_baselines.make_chunks(paths, {"f0", "f1", "f2"}, 3, seed=2)
        self.assertEqual(resumed, fresh[1:])
        # a chunk with one file missing is scored whole
        self.assertEqual(score_baselines.make_chunks(paths, {"f0", "f2"}, 3, seed=2)[0], (0, ["f0", "f1", "f2"]))

    def test_unseeded_run_chunks_only_the_files_left(self):
        import score_baselines
        self.assertEqual(score_baselines.make_chunks(["a", "b", "c"], {"a"}, 2, seed=None), [(0, ["b", "c"])])


@unittest.skipUnless(HAS_NUMPY, "needs numpy")
class VariantHelpersTest(unittest.TestCase):
    def test_credit(self):
        import utmos_speechjudge_variants as v
        self.assertEqual(v.credit(3.0, 2.0, "A"), 1.0)
        self.assertEqual(v.credit(3.0, 2.0, "B"), 0.0)
        self.assertEqual(v.credit(2.0, 2.0, "B"), 0.5)

    def test_accuracy_report_per_subset(self):
        import utmos_speechjudge_variants as v
        pairs = [
            {"path_a": "a1", "path_b": "b1", "label": "A", "subset": "regular", "sentence_id": "s1"},
            {"path_a": "a2", "path_b": "b2", "label": "A", "subset": "expressive", "sentence_id": "s2"},
        ]
        scores = {"a1": 3.0, "b1": 2.0, "a2": 1.0, "b2": 2.0}
        report = v.accuracy_report(pairs, scores)
        self.assertEqual((report["regular"], report["expressive"], report["total"], report["ties"]), (100.0, 0.0, 50.0, 0))


@unittest.skipUnless(HAS_NUMPY, "needs numpy")
class CueHelpersTest(unittest.TestCase):
    def test_bandwidth_of_a_pure_tone(self):
        import numpy
        import audio_bandwidth
        sr = 24000
        t = numpy.arange(sr) / sr
        edge, above_8k = audio_bandwidth.bandwidth(numpy.sin(2 * numpy.pi * 1000 * t).astype("float32"), sr)
        self.assertLess(abs(edge - 1000), 100)
        self.assertLess(above_8k, 1e-3)

    def test_trim_and_rms(self):
        import numpy
        import normalise_audio
        sr = 1000
        tone = numpy.sin(numpy.arange(500)).astype("float32")
        wav = numpy.concatenate([numpy.zeros(200, "float32"), tone, numpy.zeros(300, "float32")])
        self.assertEqual(len(normalise_audio.trim_edges(wav, sr)), 500)
        out = normalise_audio.change(wav, sr, "rms_trim")
        self.assertAlmostEqual(float(numpy.sqrt(numpy.mean(out.astype("float64") ** 2))), 0.05, places=4)
        self.assertEqual(len(normalise_audio.change(wav, sr, "rms")), 1000)

    def test_clip_cues(self):
        import system_cues
        feature = {"seconds": "4.0", "sample_rate": "24000", "rms": "0.1", "peak": "1.0",
                   "near_full_scale_fraction": "0.0", "leading_quiet_seconds": "0.2", "trailing_quiet_seconds": "0.1",
                   "longest_quiet_seconds": "0.5", "quiet_relative_fraction": "0.5"}
        cues = system_cues.clip_cues(feature, "ab cd")
        self.assertAlmostEqual(cues["letters_per_voiced_second"], 2.0)
        self.assertAlmostEqual(cues["rms_dbfs"], -20.0)
        self.assertAlmostEqual(cues["peak_dbfs"], 0.0)


if __name__ == "__main__":
    unittest.main()
