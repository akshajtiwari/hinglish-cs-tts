"""Checks for weighting, ties and paired uncertainty in the failure analysis."""
import unittest
import importlib.util

from scripts.step2_baselines import analyze_judge_failures as analysis


def example(identity, sentence, pairing, winner, credits):
    row = {"id":identity, "sentence_id":sentence, "pairing":pairing,
           "winner":winner, "label":"A", "mixed":True, "mean_seconds":10.0,
           "all_wrong":False, "all_right":True}
    for judge, value in zip(analysis.JUDGES, credits):
        row[judge + "_credit"] = value
    return row


class TestFailureAnalysis(unittest.TestCase):
    def test_weighting_and_winner_balance_expose_identity_shortcut(self):
        rows = []
        for index in range(10):
            winner = "X" if index < 9 else "Y"
            value = float(winner == "X")
            rows.append(example(str(index),str(index),"X vs Y",winner,[value] * 4))
        rows.append(example("10","10","Q vs R","Q",[1] * 4))
        rows.append(example("11","11","Q vs R","R",[0] * 4))
        result = analysis.summary(rows)
        self.assertAlmostEqual(result["oracle_micro"],10 / 12)
        self.assertAlmostEqual(result["oracle_macro"],0.7)
        self.assertAlmostEqual(result["utmos"]["macro"],0.7)
        self.assertAlmostEqual(result["utmos"]["winner_balanced_macro"],0.5)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "Bootstrap checks require numpy")
    def test_ties_keep_half_credit_in_replacement_difference(self):
        rows = [example("1","1","X vs Y","X",[0,1,0,0]),
                example("2","2","X vs Y","Y",[1,0,0,0]),
                example("3","3","X vs Y","X",[0.5,1,0,0])]
        result = analysis.paired_comparisons(rows,100,15)[0]
        self.assertEqual(result["fixed_strict_errors"],1)
        self.assertEqual(result["introduced_strict_errors"],1)
        self.assertEqual(result["fractional_credit_gain"],0.5)
        self.assertAlmostEqual(result["micro_difference"],1 / 6)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "Bootstrap checks require numpy")
    def test_bootstrap_keeps_related_votes_together(self):
        rows = [example("1","one_sentence","X vs Y","X",[0,1,0,0]),
                example("2","one_sentence","X vs Y","Y",[1,0,0,0])]
        result = analysis.paired_comparisons(rows,100,15)[0]
        self.assertEqual(result["sentences"],1)
        self.assertEqual(result["micro_ci95"],[0.0,0.0])

    def test_controls_keep_pairing_and_are_not_reused(self):
        failure = example("f","s","X vs Y","X",[0] * 4)
        other = example("other","s","Q vs R","X",[1] * 4)
        good = example("good","s","X vs Y","X",[1] * 4)
        results = analysis.select_controls([failure,failure],[other,good])
        self.assertEqual(results[0]["control_id"],"good")
        self.assertEqual(results[1]["control_id"],"")


if __name__ == "__main__":
    unittest.main()
