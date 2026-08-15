import unittest

from riskos.calibration import calibration_report
from riskos.challenger import challenger_scores, compare_models
from riskos.graph import graph_signals, suspicious_components
from riskos.policy import Policy, apply_policy
from riskos.simulator import generate_cases
from riskos.temporal import temporal_risk


class RiskOSAdvancedTest(unittest.TestCase):
    def setUp(self):
        self.cases = generate_cases(n=400, seed=17)

    def test_graph_signals_are_label_free_and_bounded(self):
        signals = graph_signals(self.cases)
        self.assertEqual(len(signals), len(self.cases))
        self.assertTrue(all(0.0 <= signal.graph_score <= 1.0 for signal in signals.values()))
        self.assertTrue(any(signal.component_size >= 3 for signal in signals.values()))

    def test_suspicious_components_exist(self):
        components = suspicious_components(self.cases, min_size=3)
        self.assertGreater(len(components), 0)

    def test_temporal_risk_is_bounded(self):
        scores = [temporal_risk(case) for case in self.cases]
        self.assertTrue(all(0.0 <= score <= 1.0 for score in scores))
        self.assertGreater(max(scores), 0.0)

    def test_challenger_scores_are_bounded(self):
        scores = challenger_scores(self.cases)
        self.assertEqual(len(scores), len(self.cases))
        self.assertTrue(all(0.0 <= score <= 1.0 for score in scores))

    def test_calibration_metrics_are_valid(self):
        scores = challenger_scores(self.cases)
        labels = [case.is_fraud for case in self.cases]
        report = calibration_report(scores, labels)
        self.assertGreaterEqual(report.brier_score, 0.0)
        self.assertLessEqual(report.brier_score, 1.0)
        self.assertGreaterEqual(report.expected_calibration_error, 0.0)
        self.assertLessEqual(report.expected_calibration_error, 1.0)

    def test_champion_challenger_comparison_runs(self):
        comparison, champion_cal, challenger_cal = compare_models(self.cases)
        self.assertGreater(comparison.champion_mean_fraud_score, comparison.champion_mean_benign_score)
        self.assertGreater(comparison.challenger_mean_fraud_score, comparison.challenger_mean_benign_score)
        self.assertEqual(len(champion_cal.bins), 10)
        self.assertEqual(len(challenger_cal.bins), 10)

    def test_policy_records_version_and_reasons(self):
        record = apply_policy(
            entity_id="carrier_test",
            score=0.82,
            exposure_usd=10000,
            reason_codes=["velocity_spike", "shared_device_cluster"],
            policy=Policy(version="test-v1"),
        )
        self.assertEqual(record.action, "REVIEW")
        self.assertEqual(record.policy_version, "test-v1")
        self.assertEqual(len(record.reason_codes), 2)


if __name__ == "__main__":
    unittest.main()
