"""FastAPI service for RiskOS scoring and policy decisions."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from riskos.core import EntityFeatures, behavior_risk, graph_risk, reasons, risk_score
from riskos.policy import apply_policy


app = FastAPI(title="RiskOS API", version="0.2.0")


class ScoreRequest(BaseModel):
    entity_id: str
    account_age_days: int = Field(ge=0)
    new_device: int = Field(ge=0, le=1)
    bank_change_24h: int = Field(ge=0, le=1)
    velocity_ratio: float = Field(ge=0)
    shared_device_count: int = Field(ge=0)
    suspended_neighbor_count: int = Field(ge=0)
    exposure_usd: float = Field(ge=0)
    suspicious_sequence: int = Field(ge=0, le=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "riskos"}


@app.post("/score")
def score(request: ScoreRequest) -> dict[str, object]:
    features = EntityFeatures(**request.model_dump())
    score_value = risk_score(features)
    reason_codes = reasons(features)
    record = apply_policy(
        entity_id=features.entity_id,
        score=score_value,
        exposure_usd=features.exposure_usd,
        reason_codes=reason_codes,
    )
    return {
        "entity_id": features.entity_id,
        "risk_score": score_value,
        "behavior_risk": behavior_risk(features),
        "graph_feature_risk": graph_risk(features),
        "decision": record.to_dict(),
    }
