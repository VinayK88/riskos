"""Lightweight score-distribution monitoring for RiskOS."""

from math import log
from statistics import mean


def _bucket_index(value: float, cuts: list[float]) -> int:
    for idx, upper in enumerate(cuts):
        if value <= upper:
            return idx
    return len(cuts)


def population_stability_index(
    reference: list[float],
    current: list[float],
    cuts: list[float] | None = None,
    epsilon: float = 1e-6,
) -> float:
    """Compute PSI for two bounded score distributions."""
    if not reference or not current:
        raise ValueError("reference and current distributions must be non-empty")

    cuts = cuts or [0.2, 0.4, 0.6, 0.8]
    bucket_count = len(cuts) + 1
    ref_counts = [0] * bucket_count
    cur_counts = [0] * bucket_count

    for value in reference:
        ref_counts[_bucket_index(value, cuts)] += 1
    for value in current:
        cur_counts[_bucket_index(value, cuts)] += 1

    psi = 0.0
    for ref_count, cur_count in zip(ref_counts, cur_counts):
        ref_pct = max(ref_count / len(reference), epsilon)
        cur_pct = max(cur_count / len(current), epsilon)
        psi += (cur_pct - ref_pct) * log(cur_pct / ref_pct)
    return psi


def drift_summary(reference: list[float], current: list[float]) -> dict[str, float | str]:
    psi = population_stability_index(reference, current)
    if psi < 0.10:
        status = "stable"
    elif psi < 0.25:
        status = "watch"
    else:
        status = "investigate"

    return {
        "psi": psi,
        "mean_score_reference": mean(reference),
        "mean_score_current": mean(current),
        "mean_score_shift": mean(current) - mean(reference),
        "high_risk_rate_reference": sum(score >= 0.4 for score in reference) / len(reference),
        "high_risk_rate_current": sum(score >= 0.4 for score in current) / len(current),
        "status": status,
    }
