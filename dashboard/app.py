"""Interactive RiskOS trust-and-safety dashboard.

Run from the repository root:
    streamlit run dashboard/app.py
"""

import pandas as pd
import streamlit as st

from riskos.core import decision, expected_loss, reasons, risk_score
from riskos.evaluation import best_threshold, threshold_sweep
from riskos.monitoring import drift_summary
from riskos.simulator import generate_cases


st.set_page_config(page_title="RiskOS", page_icon="🛡️", layout="wide")
st.title("RiskOS — Trust & Safety Decisioning")
st.caption("Synthetic marketplace risk, review-capacity optimization, and drift monitoring")

sample_size = st.sidebar.slider("Synthetic entities", 200, 1500, 600, step=100)
fraud_rate = st.sidebar.slider("Fraud prevalence", 0.05, 0.30, 0.125, step=0.005)
review_capacity = st.sidebar.slider("Analyst review capacity", 20, 250, 60, step=5)

cases = generate_cases(n=sample_size, fraud_rate=fraud_rate, seed=17)
rows = threshold_sweep(cases, review_capacity=review_capacity)
best = best_threshold(cases, review_capacity=review_capacity)

scored = []
for case in cases:
    score = risk_score(case.features)
    scored.append(
        {
            "entity": case.features.entity_id,
            "label": "fraud" if case.is_fraud else "legitimate",
            "ring": case.ring_id or "—",
            "risk": score,
            "action": decision(score, case.features.exposure_usd),
            "exposure_usd": case.features.exposure_usd,
            "expected_loss": expected_loss(score, case.features.exposure_usd),
            "reasons": ", ".join(reasons(case.features)),
        }
    )

score_df = pd.DataFrame(scored).sort_values("expected_loss", ascending=False)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Selected threshold", f"{best.threshold:.2f}")
m2.metric("Fraud recall", f"{best.recall:.1%}")
m3.metric("Precision", f"{best.precision:.1%}")
m4.metric("Reviews", f"{best.review_count} / {review_capacity}")

tab1, tab2, tab3 = st.tabs(["Decision queue", "Threshold economics", "Model monitoring"])

with tab1:
    st.subheader("Exposure-aware analyst queue")
    st.write(
        "Cases are ranked by expected loss so a moderately risky high-exposure case can "
        "outrank a nearly certain low-exposure case."
    )
    st.dataframe(
        score_df.head(50),
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk": st.column_config.ProgressColumn(
                "risk", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "exposure_usd": st.column_config.NumberColumn("exposure_usd", format="$%.0f"),
            "expected_loss": st.column_config.NumberColumn("expected_loss", format="$%.0f"),
        },
    )

with tab2:
    st.subheader("Threshold selection is an operating decision")
    sweep_df = pd.DataFrame(
        [
            {
                "threshold": row.threshold,
                "precision": row.precision,
                "recall": row.recall,
                "f1": row.f1,
                "reviews": row.review_count,
                "total_cost": row.total_cost,
                "feasible": row.review_count <= review_capacity,
            }
            for row in rows
        ]
    )
    st.line_chart(sweep_df.set_index("threshold")[["precision", "recall", "f1"]])
    st.line_chart(sweep_df.set_index("threshold")[["total_cost"]])
    st.dataframe(sweep_df, use_container_width=True, hide_index=True)
    st.info(
        f"Selected threshold: {best.threshold:.2f}. RiskOS minimizes expected operating cost "
        "only among thresholds that fit the configured analyst review capacity."
    )

with tab3:
    st.subheader("Prediction-distribution drift")
    reference_cases = generate_cases(n=sample_size, fraud_rate=0.125, seed=17)
    shifted_cases = generate_cases(
        n=sample_size,
        fraud_rate=min(0.35, fraud_rate + 0.08),
        seed=91,
    )
    reference_scores = [risk_score(case.features) for case in reference_cases]
    shifted_scores = [risk_score(case.features) for case in shifted_cases]
    summary = drift_summary(reference_scores, shifted_scores)

    d1, d2, d3 = st.columns(3)
    d1.metric("PSI", f"{summary['psi']:.3f}")
    d2.metric("Mean-score shift", f"{summary['mean_score_shift']:+.3f}")
    d3.metric("Status", str(summary["status"]).upper())

    bins = [0, 0.2, 0.4, 0.6, 0.8, 1]
    dist_df = pd.DataFrame(
        {
            "reference": pd.cut(reference_scores, bins=bins, include_lowest=True).value_counts(sort=False),
            "shifted": pd.cut(shifted_scores, bins=bins, include_lowest=True).value_counts(sort=False),
        }
    )
    st.bar_chart(dist_df)
    st.caption("PSI < 0.10: stable · 0.10–0.25: watch · ≥ 0.25: investigate")

st.divider()
st.caption("All events and labels are synthetic. No production enforcement or customer data is used.")
