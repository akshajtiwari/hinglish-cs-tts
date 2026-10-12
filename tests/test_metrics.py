import math
import unittest

from switchmos.eval import metrics


class TestMetrics(unittest.TestCase):
    def test_rankdata_averages_ties(self):
        self.assertEqual(metrics.rankdata([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])
        self.assertEqual(metrics.rankdata([3, 1, 2]), [3.0, 1.0, 2.0])

    def test_pearson_and_spearman_known_values(self):
        self.assertAlmostEqual(metrics.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(metrics.pearson([1, 2, 3], [3, 2, 1]), -1.0)
        # monotone but not linear: Spearman 1, Pearson below 1
        x = [1, 2, 3, 4]
        y = [1, 4, 9, 100]
        self.assertAlmostEqual(metrics.spearman(x, y), 1.0)
        self.assertLess(metrics.pearson(x, y), 1.0)
        # scipy.stats.spearmanr([1,2,3,4,5],[5,6,7,8,7]) == 0.8207826816681233
        self.assertAlmostEqual(metrics.spearman([1, 2, 3, 4, 5], [5, 6, 7, 8, 7]), 0.8207826816681233)

    def test_constant_input_gives_nan(self):
        self.assertTrue(math.isnan(metrics.pearson([1, 1, 1], [1, 2, 3])))

    def test_mse(self):
        self.assertAlmostEqual(metrics.mse([1, 2], [2, 4]), 2.5)

    def test_system_level_uses_means(self):
        pred = [1.0, 3.0, 4.0, 4.0]
        true = [2.0, 2.0, 5.0, 3.0]
        report = metrics.regression_report(pred, true, systems=["s1", "s1", "s2", "s2"])
        self.assertEqual(report["n_systems"], 2)
        self.assertAlmostEqual(report["sys_srcc"], 1.0)            # s1: pred 2 vs true 2; s2: pred 4 vs true 4
        self.assertAlmostEqual(report["sys_mse"], 0.0)

    def test_pairwise_accuracy(self):
        self.assertAlmostEqual(metrics.pairwise_accuracy([3, 1, 2], [1, 2, 2], ["A", "B", "A"]), (1 + 1 + 0.5) / 3)


if __name__ == "__main__":
    unittest.main()
