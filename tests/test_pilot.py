import unittest

from switchmos import pilot


class TestPilot(unittest.TestCase):
    def test_clip_mean_targets(self):
        means = pilot.clip_mean_targets(["a", "b", "a"], [1.0, 4.0, 3.0])
        self.assertEqual(means, {"a": 2.0, "b": 4.0})

    def test_page_normalised_targets(self):
        # page p1: scores 20 and 80 -> z -1 and +1; page p2: one score -> 0
        targets = pilot.page_normalised_targets(["x", "y", "x"], ["p1", "p1", "p2"], [20.0, 80.0, 50.0])
        self.assertAlmostEqual(targets["y"], 1.0)
        self.assertAlmostEqual(targets["x"], -0.5)      # mean of -1 (page p1) and 0 (page p2)

    def test_page_without_spread_gives_zero(self):
        targets = pilot.page_normalised_targets(["x", "y"], ["p", "p"], [60.0, 60.0])
        self.assertEqual(targets, {"x": 0.0, "y": 0.0})

    def test_selection_score(self):
        metrics = {"speechjudge_val_accuracy": 0.7, "bvcc_val_srcc": 0.8, "somos_val_srcc": 0.4, "mango_val_srcc": 0.5}
        self.assertAlmostEqual(pilot.selection_score(metrics), 0.6)
        metrics["mango_val_srcc"] = float("nan")
        self.assertIsNone(pilot.selection_score(metrics))
        del metrics["mango_val_srcc"]
        self.assertIsNone(pilot.selection_score(metrics))


if __name__ == "__main__":
    unittest.main()
