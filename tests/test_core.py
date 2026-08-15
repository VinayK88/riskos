import unittest

from riskos.core import EntityFeatures, decision, expected_loss, risk_score


class RiskOSTest(unittest.TestCase):
    def test_high_risk_entity_scores_above_benign(self):
        benign = EntityFeatures("benign", 500, 0, 0, 1.0, 0, 0, 1000, 0)
        risky = EntityFeatures("risky", 3, 1, 1, 6.0, 4, 3, 20000, 1)
        self.assertGreater(risk_score(risky), risk_score(benign))

    def test_expected_loss(self):
        self.assertEqual(expected_loss(0.8, 10000), 8000)

    def test_policy_actions(self):
        self.assertEqual(decision(0.97, 1000), "BLOCK")
        self.assertEqual(decision(0.82, 1000), "REVIEW")
        self.assertEqual(decision(0.65, 10000), "CHALLENGE")
        self.assertEqual(decision(0.20, 10000), "ALLOW")


if __name__ == "__main__":
    unittest.main()
