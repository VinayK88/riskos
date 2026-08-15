"""Versioned policy engine and auditable decision records."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(frozen=True)
class Policy:
    version: str = "2026.08"
    block_threshold: float = 0.95
    review_threshold: float = 0.78
    challenge_threshold: float = 0.60
    challenge_exposure_usd: float = 5000.0


@dataclass(frozen=True)
class DecisionRecord:
    entity_id: str
    score: float
    exposure_usd: float
    action: str
    policy_version: str
    reason_codes: tuple[str, ...]
    decided_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def apply_policy(
    entity_id: str,
    score: float,
    exposure_usd: float,
    reason_codes: list[str],
    policy: Policy | None = None,
) -> DecisionRecord:
    policy = policy or Policy()
    if score >= policy.block_threshold:
        action = "BLOCK"
    elif score >= policy.review_threshold:
        action = "REVIEW"
    elif score >= policy.challenge_threshold and exposure_usd >= policy.challenge_exposure_usd:
        action = "CHALLENGE"
    else:
        action = "ALLOW"

    return DecisionRecord(
        entity_id=entity_id,
        score=score,
        exposure_usd=exposure_usd,
        action=action,
        policy_version=policy.version,
        reason_codes=tuple(reason_codes),
        decided_at=datetime.now(timezone.utc).isoformat(),
    )
