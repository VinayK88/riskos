from riskos.core import decision, expected_loss, reasons, risk_score
from riskos.simulator import generate_cases


def main() -> None:
    cases = generate_cases(n=80, seed=23)
    ranked = []

    for case in cases:
        entity = case.features
        score = risk_score(entity)
        ranked.append((expected_loss(score, entity.exposure_usd), case, score))

    ranked.sort(reverse=True, key=lambda row: row[0])

    print("RiskOS synthetic marketplace review queue")
    print("-" * 90)
    for loss, case, score in ranked[:12]:
        entity = case.features
        print(
            f"entity={entity.entity_id:12s} "
            f"risk={score:.2f} "
            f"action={decision(score, entity.exposure_usd):9s} "
            f"expected_loss=${loss:,.0f} "
            f"label={'fraud' if case.is_fraud else 'legitimate'}"
        )
        print("reasons=" + ", ".join(reasons(entity)))


if __name__ == "__main__":
    main()
