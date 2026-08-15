import unittest

from riskos.core import risk_score
from riskos.evaluation import best_threshold, evaluate_threshold
from riskos.monitoring import drift_summary, population_stability_index
from riskos.simulator import generate_cases


class RiskOSScienceTest(unittest.TestCase):
    def test_simulator_is_deterministic(self):
        a = generate_cases(n=100, seed=9)
        b = generate_cases(n=100, seed=9)
        self.assertEqual(a, b)

    def test_default_fixture_has_expected_prevalence(self):
        cases = generate_cases()
        self.assertEqual(sum(case.is_fraud for case in cases), 75)

    def test_fraud_population_scores_higher_on_average(self):
        cases = generate_cases()
        fraud_scores = [risk_score(c.features) for c in cases if c.is_fraud]
        benign_scores = [risk_score(c.features) for c in cases if not c.is_fraud]
        self.assertGreater(sum(fraud_scores) / len(fraud_scores), sum(benign_scores) / len(benign_scores))

    def test_threshold_metrics_are_bounded(self):
        result = evaluate_threshold(generate_cases(n=300), 0.40, review_capacity=35)
        self.assertGreaterEqual(result.precision, 0.0)
        self.assertLessEqual(result.precision, 1.0)
        self.assertGreaterEqual(result.recall, 0.0)
        self.assertLessEqual(result.recall, 1.0)
        self.assertGreaterEqual(result.total_cost, 0.0)

    def test_selected_threshold_respects_capacity(self):
        best = best_threshold(generate_cases(), review_capacity=60)
        self.assertLessEqual(best.review_count, 60)

    def test_psi_detects_distribution_shift(self):
        stable = [0.1, 0.15, 0.2, 0.35, 0.5, 0.7, 0.85] * 10
        shifted = [0.65, 0.72, 0.81, 0.88, 0.91, 0.94, 0.97] * 10
        self.assertLess(population_stability_index(stable, stable), 0.001)
        self.assertGreater(population_stability_index(stable, shifted), 0.25)
        self.assertEqual(drift_summary(stable, shifted)["status"], "investigate")


if __name__ == "__main__":
    unittest.main()
