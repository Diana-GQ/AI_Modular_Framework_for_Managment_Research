"""The competition's weighted score of one evaluation."""

CRITERIA = ("concept", "business_model", "market", "written_work", "investor_interest")


def run(inputs: dict, settings: dict) -> dict:
    scores, weights = inputs["scores"], settings["weights"]
    if abs(sum(weights[c] for c in CRITERIA) - 1) > 1e-9:
        raise ValueError("weights must sum to 1")
    return {"weighted_score": round(sum(weights[c] * float(scores[c]) for c in CRITERIA), 6)}
