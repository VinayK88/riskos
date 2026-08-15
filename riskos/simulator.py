"""Deterministic synthetic marketplace generator for RiskOS."""

from dataclasses import dataclass
from random import Random

from riskos.core import EntityFeatures


@dataclass(frozen=True)
class SyntheticCase:
    features: EntityFeatures
    is_fraud: int
    ring_id: str | None


def generate_cases(n: int = 600, fraud_rate: float = 0.14, seed: int = 17) -> list[SyntheticCase]:
    """Generate labeled marketplace entities with benign and fraud-ring behavior.

    Labels are synthetic and intentionally learnable. This function validates
    evaluation plumbing; it does not estimate production fraud rates.
    """
    rng = Random(seed)
    cases: list[SyntheticCase] = []

    for idx in range(n):
        fraud = int(rng.random() < fraud_rate)
        ring_id = f"ring_{rng.randint(1, 8):02d}" if fraud and rng.random() < 0.72 else None

        if fraud:
            account_age = rng.randint(1, 90)
            new_device = int(rng.random() < 0.72)
            bank_change = int(rng.random() < 0.58)
            velocity = round(rng.uniform(2.4, 8.5), 2)
            shared_devices = rng.randint(1, 6) if ring_id else rng.randint(0, 3)
            suspended_neighbors = rng.randint(1, 4) if ring_id else rng.randint(0, 2)
            exposure = round(rng.uniform(4000, 85000), 2)
            suspicious_sequence = int(rng.random() < 0.68)
        else:
            account_age = rng.randint(30, 1200)
            new_device = int(rng.random() < 0.10)
            bank_change = int(rng.random() < 0.04)
            velocity = round(max(0.3, rng.gauss(1.05, 0.38)), 2)
            shared_devices = 1 if rng.random() < 0.07 else 0
            suspended_neighbors = 1 if rng.random() < 0.015 else 0
            exposure = round(rng.uniform(100, 30000), 2)
            suspicious_sequence = int(rng.random() < 0.025)

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
