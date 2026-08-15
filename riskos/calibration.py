"""Calibration diagnostics for trust-and-safety risk scores."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationBin:
    lower: float
    upper: float
    count: int
    mean_score: float
    fraud_rate: float


@dataclass(frozen=True)
class CalibrationReport:
    brier_score: float
    expected_calibration_error: float
    bins: tuple[CalibrationBin, ...]


def calibration_report(scores: list[float], labels: list[int], bins: int = 10) -> CalibrationReport:
    if len(scores) != len(labels) or not scores:
        raise ValueError("scores and labels must be non-empty and have equal length")

    brier = sum((score - label) ** 2 for score, label in zip(scores, labels)) / len(scores)
    output: list[CalibrationBin] = []
    ece = 0.0

    for idx in range(bins):
        lower = idx / bins
        upper = (idx + 1) / bins
        selected = [
            (score, label)
            for score, label in zip(scores, labels)
            if lower <= score < upper or (idx == bins - 1 and score == 1.0)
        ]
        if not selected:
            output.append(CalibrationBin(lower, upper, 0, 0.0, 0.0))
            continue
        mean_score = sum(score for score, _ in selected) / len(selected)
        fraud_rate = sum(label for _, label in selected) / len(selected)
        weight = len(selected) / len(scores)
        ece += weight * abs(mean_score - fraud_rate)
        output.append(CalibrationBin(lower, upper, len(selected), mean_score, fraud_rate))

    return CalibrationReport(brier, ece, tuple(output))
