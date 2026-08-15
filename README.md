<div align="center">

# 🛡️ RiskOS

### Real-Time Trust & Safety Decisioning Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/VinayK88/riskos/actions/workflows/ci.yml/badge.svg)](https://github.com/VinayK88/riskos/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-scoring%20service-009688?logo=fastapi)](api/app.py)
[![Streamlit](https://img.shields.io/badge/Streamlit-analyst%20workbench-FF4B4B?logo=streamlit&logoColor=white)](dashboard/app.py)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Mode](https://img.shields.io/badge/Data-synthetic%20only-7B61FF)](#safety-and-scope)

**Simulate → link → sequence → score → calibrate → decide → monitor → learn**

</div>

---

RiskOS is a reproducible marketplace trust-and-safety decisioning platform built around a harder production question than **“is this fraud?”**:

> **Given uncertain model scores, entity relationships, ordered behavior, financial exposure, customer-friction cost, and finite analyst capacity, which entities should be allowed, challenged, reviewed, or blocked?**

The repository demonstrates the full loop: synthetic marketplace generation, behavioral scoring, label-free entity-link graph analysis, temporal sequence detection, champion/challenger experimentation, calibration diagnostics, expected-loss prioritization, capacity-aware threshold optimization, versioned policy decisions, drift monitoring, an analyst dashboard, an API boundary, Docker packaging, tests, and CI.

## Why this project is different

Most portfolio fraud projects end at AUC or accuracy. RiskOS models the **operating system around the model**:

- overlapping benign and fraud populations rather than perfectly separable labels;
- behavioral, graph, temporal, and exposure signals;
- explicit shared device / bank / IP infrastructure;
- graph clusters computed without reading synthetic fraud labels;
- ordered event-sequence detection for account takeover / monetization patterns;
- champion/challenger scoring and calibration diagnostics (Brier score + ECE);
- expected-loss ranking so analyst attention follows risk *and* exposure;
- **ALLOW / CHALLENGE / REVIEW / BLOCK** outcomes;
- hard analyst-capacity constraints when selecting operating thresholds;
- versioned policy decisions with reason codes and UTC audit timestamps;
- PSI-based score drift monitoring;
- FastAPI scoring service + Docker image;
- deterministic synthetic fixtures, unit tests, and GitHub Actions CI.

## Architecture

```mermaid
flowchart LR
    SIM["Synthetic marketplace\nentities + fraud rings"] --> FEAT["Behavior + velocity\nfeatures"]
    SIM --> LINK["Device · Bank · IP\nentity graph"]
    SIM --> SEQ["Ordered event\nsequences"]

    FEAT --> CHAMP["Champion score"]
    LINK --> GS["Graph signals"]
    SEQ --> TS["Temporal risk"]
    CHAMP & GS & TS --> CHAL["Challenger model"]

    CHAMP & CHAL --> CAL["Calibration\nBrier + ECE"]
    CHAMP --> ECON["Expected-loss +\ncapacity optimization"]
    ECON --> POLICY{"Versioned policy"}

    POLICY --> ALLOW["ALLOW"]
    POLICY --> CHALLENGE["CHALLENGE"]
    POLICY --> REVIEW["REVIEW"]
    POLICY --> BLOCK["BLOCK"]

    REVIEW --> HUMAN["Analyst queue"]
    HUMAN --> MON["Monitoring + feedback"]
    MON -. "recalibrate / retune" .-> POLICY

    POLICY --> API["FastAPI"]
    CHAMP & GS & TS & CAL & MON --> UI["Streamlit workbench"]
```

## Entity-link graph intelligence

Synthetic entities receive opaque `device_id`, `bank_id`, and `ip_id` values. Fraud-ring members often reuse infrastructure, while a small benign shared-infrastructure population creates graph noise.

`riskos/graph.py` builds a relationship graph and calculates:

- connected-component size;
- peer count;
- number of shared infrastructure resources;
- bounded graph risk;
- suspicious connected components.

The graph scorer **does not consume `is_fraud` or `ring_id`**. Those labels exist only to evaluate whether link analysis recovers hidden synthetic relationships.

## Temporal risk

`riskos/temporal.py` derives ordered event streams such as:

```text
session_start
  → new_device
  → bank_change
  → velocity_spike
  → counterparty_spike
  → high_value_action
```

RiskOS scores suspicious sequences only when the events occur in order and within a bounded time window. This demonstrates why point-in-time features can miss behavior that becomes meaningful only as a sequence.

## Champion / challenger model lab

The **champion** is the original interpretable behavioral risk engine.

The **challenger** combines:

```text
62% champion behavioral score
23% label-free graph risk
15% temporal sequence risk
```

`riskos/calibration.py` evaluates both systems using:

- Brier score;
- Expected Calibration Error (ECE);
- reliability bins comparing average score vs. observed synthetic fraud rate.

The point is not to assume a more complex model is better. RiskOS explicitly checks whether improved separation also produces probability estimates that are trustworthy enough for decisioning.

## Decision economics

A probability alone is not the decision.

RiskOS prioritizes review using:

```text
expected_loss = risk_score × financial_exposure
```

Threshold selection minimizes an illustrative operating objective:

```text
expected operating cost =
    missed fraud loss
  + false-positive / customer-friction cost
  + analyst review cost
  + queue-overflow penalty
```

The final recommended threshold must also satisfy a **hard analyst review-capacity constraint**.

### Checked-in deterministic baseline

The committed fixture contains 600 synthetic entities using seed `17`. Under the illustrative operating assumptions in [`reports/baseline-evaluation.json`](reports/baseline-evaluation.json):

| Metric | Result |
| --- | ---: |
| Synthetic entities | 600 |
| Synthetic fraud cases | 75 |
| Synthetic fraud-ring members | 45 |
| Analyst review capacity | 60 |
| Recommended threshold | **0.40** |
| Precision | **94.9%** |
| Recall | **74.7%** |
| F1 | **83.6%** |
| Review volume | **59 / 60** |
| False positives | **3** |

These values validate deterministic code paths and operating tradeoffs. They are **not production performance claims**.

## Versioned policy and audit trail

`riskos/policy.py` separates model scoring from operational policy. Every policy decision records:

```text
entity_id
risk score
exposure
ALLOW / CHALLENGE / REVIEW / BLOCK
policy version
reason codes
UTC decision timestamp
```

That separation makes it possible to change thresholds, test policies, roll back decisions, and preserve an auditable record without retraining the model.

## Analyst workbench

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

The dashboard now has five views:

1. **Decision queue** — exposure-aware case ranking, reason codes, graph and temporal risk.
2. **Threshold economics** — precision/recall/F1, review volume, capacity feasibility, total operating cost.
3. **Entity graph** — shared-resource signals and connected clusters.
4. **Model lab** — champion/challenger Brier score, ECE, and reliability bins.
5. **Monitoring** — reference-vs-shifted score distributions and PSI state.

## Scoring API

Install the API dependencies:

```bash
python -m pip install -r requirements-api.txt
uvicorn api.app:app --reload
```

Endpoints:

```text
GET  /health
POST /score
```

The `/score` endpoint returns the overall risk score, behavioral component, graph-feature component, and a versioned policy decision with reason codes.

### Docker

```bash
docker build -t riskos .
docker run --rm -p 8000:8000 riskos
```

## Dependency-free research path

The core analytics require only the Python standard library:

```bash
python -m riskos.demo
python -m riskos.evaluation
python -m riskos.challenger
python -m unittest discover -s tests -v
```

## Project map

```text
riskos/
├── README.md
├── LICENSE
├── Dockerfile
├── pyproject.toml
├── requirements-api.txt
├── requirements-dashboard.txt
│
├── api/
│   └── app.py
│
├── dashboard/
│   └── app.py
│
├── reports/
│   └── baseline-evaluation.json
│
├── riskos/
│   ├── core.py
│   ├── simulator.py
│   ├── graph.py
│   ├── temporal.py
│   ├── challenger.py
│   ├── calibration.py
│   ├── policy.py
│   ├── evaluation.py
│   ├── monitoring.py
│   └── demo.py
│
├── tests/
│   ├── test_core.py
│   ├── test_science.py
│   └── test_advanced.py
│
└── .github/workflows/ci.yml
```

## Production evolution

A production implementation would replace synthetic fixtures with privacy-reviewed event streams and add:

- online/offline feature consistency and event-time windows;
- a scalable entity graph store and incremental graph features;
- calibrated supervised + anomaly models;
- champion/challenger shadow deployment;
- delayed-label handling and analyst-feedback learning;
- policy versioning backed by durable audit storage;
- subgroup / fairness guardrails and customer-impact reviews;
- feature/data quality contracts;
- rollback and threshold kill switches;
- service-level latency, throughput, and availability monitoring.

## Safety and scope

All identities, labels, graph relationships, exposures, and cost assumptions are synthetic. RiskOS does not connect to real marketplace accounts, payment systems, bank data, customer records, or enforcement systems. It is a defensive trust-and-safety research and portfolio project, not a production fraud service.
