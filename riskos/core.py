from dataclasses import dataclass
from math import exp


@dataclass
class EntityFeatures:
    entity_id: str
    account_age_days: int
    new_device: int
    bank_change_24h: int
    velocity_ratio: float
    shared_device_count: int
    suspended_neighbor_count: int
    exposure_usd: float
    suspicious_sequence: int


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


def behavior_risk(f: EntityFeatures) -> float:
    score = (
        -2.4
        + 0.9 * f.new_device
        + 1.1 * f.bank_change_24h
        + 0.45 * max(0.0, f.velocity_ratio - 1.0)
        + 1.0 * f.suspicious_sequence
        - 0.004 * min(f.account_age_days, 365)
    )
    return _sigmoid(score)


def graph_risk(f: EntityFeatures) -> float:
    score = -2.2 + 0.55 * f.shared_device_count + 0.95 * f.suspended_neighbor_count
    return _sigmoid(score)


def risk_score(f: EntityFeatures) -> float:
    behavior = behavior_risk(f)
    graph = graph_risk(f)
    exposure_component = min(f.exposure_usd / 50000.0, 1.0)
    fused = 0.55 * behavior + 0.35 * graph + 0.10 * exposure_component
    return min(max(fused, 0.0), 1.0)


def decision(score: float, exposure_usd: float) -> str:
    if score >= 0.95:
        return "BLOCK"
    if score >= 0.78:
        return "REVIEW"
    if score >= 0.60 and exposure_usd >= 5000:
        return "CHALLENGE"
    return "ALLOW"


def expected_loss(score: float, exposure_usd: float) -> float:
    return score * exposure_usd


def reasons(f: EntityFeatures) -> list[str]:
    items = []
    if f.suspended_neighbor_count:
        items.append("linked_to_suspended_entities")
    if f.shared_device_count >= 2:
        items.append("shared_device_cluster")
    if f.bank_change_24h:
        items.append("bank_change_24h")
    if f.velocity_ratio >= 3:
        items.append("velocity_spike")
    if f.new_device:
        items.append("new_device")
    if f.suspicious_sequence:
        items.append("suspicious_action_sequence")
    return items or ["no_material_risk_signal"]
