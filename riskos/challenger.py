"""Champion/challenger scoring for RiskOS."""

from dataclasses import dataclass

from riskos.calibration import CalibrationReport, calibration_report
from riskos.core import risk_score
from riskos.graph import graph_signals
from riskos.simulator import SyntheticCase
from riskos.temporal import temporal_risk


@dataclass(frozen=True)
class ModelComparison:
    champion_brier: float
    challenger_brier: float
    champion_ece: float
    challenger_ece: float
    champion_mean_fraud_score: float
    challenger_mean_fraud_score: float
    champion_mean_benign_score: float
    challenger_mean_benign_score: float


def challenger_scores(cases: list[SyntheticCase]) -> list[float]:
    graph = graph_signals(cases)
    scores: list[float] = []
    for case in cases:
        base = risk_score(case.features)
        network = graph[case.features.entity_id].graph_score
        temporal = temporal_risk(case)
        score = 0.62 * base + 0.23 * network + 0.15 * temporal
        scores.append(min(max(score, 0.0), 1.0))
    return scores


def compare_models(cases: list[SyntheticCase]) -> tuple[ModelComparison, CalibrationReport, CalibrationReport]:
    labels = [case.is_fraud for case in cases]
    champion = [risk_score(case.features) for case in cases]
    challenger = challenger_scores(cases)
    champion_cal = calibration_report(champion, labels)
    challenger_cal = calibration_report(challenger, labels)

    def mean_for(scores: list[float], label: int) -> float:
        selected = [score for score, actual in zip(scores, labels) if actual == label]
        return sum(selected) / len(selected)

    comparison = ModelComparison(
        champion_brier=champion_cal.brier_score,
        challenger_brier=challenger_cal.brier_score,
        champion_ece=champion_cal.expected_calibration_error,
        challenger_ece=challenger_cal.expected_calibration_error,
        champion_mean_fraud_score=mean_for(champion, 1),
        challenger_mean_fraud_score=mean_for(challenger, 1),
        champion_mean_benign_score=mean_for(champion, 0),
        challenger_mean_benign_score=mean_for(challenger, 0),
    )
    return comparison, champion_cal, challenger_cal


def main() -> None:
    from riskos.simulator import generate_cases

    comparison, _, _ = compare_models(generate_cases())
    print("RiskOS champion/challenger calibration")
    print(f"champion_brier={comparison.champion_brier:.4f}")
    print(f"challenger_brier={comparison.challenger_brier:.4f}")
    print(f"champion_ece={comparison.champion_ece:.4f}")
    print(f"challenger_ece={comparison.challenger_ece:.4f}")
    print(f"champion_fraud_mean={comparison.champion_mean_fraud_score:.3f}")
    print(f"challenger_fraud_mean={comparison.challenger_mean_fraud_score:.3f}")


if __name__ == "__main__":
    main()
