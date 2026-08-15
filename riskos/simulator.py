"""Deterministic synthetic marketplace generator for RiskOS."""

from dataclasses import dataclass
from random import Random

from riskos.core import EntityFeatures


@dataclass(frozen=True)
class SyntheticCase:
    features: EntityFeatures
    is_fraud: int
    ring_id: str | None


def generate_cases(n: int = 600, fraud_rate: float = 0.125, seed: int = 17) -> list[SyntheticCase]:
    """Generate overlapping benign and fraud populations.

    The simulator creates a fixed fraud prevalence, a mix of obvious and stealthy
    fraud, and a small operationally unusual legitimate segment. The objective is
    to exercise realistic threshold tradeoffs, not to estimate production fraud.
    """
    rng = Random(seed)
    fraud_count = round(n * fraud_rate)
    fraud_indices = set(rng.sample(range(n), fraud_count))
    cases: list[SyntheticCase] = []

    for idx in range(n):
        fraud = int(idx in fraud_indices)
        ring_id = f"ring_{rng.randint(1, 8):02d}" if fraud and rng.random() < 0.63 else None

        if fraud:
            stealthy = rng.random() < 0.30
            account_age = rng.randint(10, 420) if stealthy else rng.randint(1, 120)
            new_device = int(rng.random() < (0.35 if stealthy else 0.62))
            bank_change = int(rng.random() < (0.22 if stealthy else 0.48))
            velocity = round(
                rng.uniform(1.0, 3.2) if stealthy else rng.uniform(2.0, 7.0),
                2,
            )
            shared_devices = rng.randint(1, 4) if ring_id else rng.randint(0, 2)
            suspended_neighbors = (
                rng.randint(1, 3)
                if ring_id and rng.random() < 0.72
                else rng.randint(0, 1)
            )
            exposure = round(rng.uniform(3000, 85000), 2)
            suspicious_sequence = int(rng.random() < (0.20 if stealthy else 0.58))
        else:
            unusual = rng.random() < 0.12
            account_age = rng.randint(20, 1200)
            new_device = int(rng.random() < (0.45 if unusual else 0.08))
            bank_change = int(rng.random() < (0.25 if unusual else 0.03))
            velocity = round(
                rng.uniform(1.8, 4.5)
                if unusual
                else max(0.3, rng.gauss(1.05, 0.42)),
                2,
            )
            shared_devices = rng.randint(0, 3) if unusual else (1 if rng.random() < 0.07 else 0)
            suspended_neighbors = 1 if unusual and rng.random() < 0.18 else 0
            exposure = round(rng.uniform(100, 55000 if unusual else 30000), 2)
            suspicious_sequence = int(rng.random() < (0.14 if unusual else 0.02))

        features = EntityFeatures(
            entity_id=f"carrier_{idx:04d}",
            account_age_days=account_age,
            new_device=new_device,
            bank_change_24h=bank_change,
            velocity_ratio=velocity,
            shared_device_count=shared_devices,
            suspended_neighbor_count=suspended_neighbors,
            exposure_usd=exposure,
            suspicious_sequence=suspicious_sequence,
        )
        cases.append(SyntheticCase(features, fraud, ring_id))

    return cases
