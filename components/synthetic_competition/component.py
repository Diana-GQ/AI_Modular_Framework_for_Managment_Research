"""The synthetic competition's design (design, B4): fictional ventures with
their form answers and a hidden quality and quality of writing, fictional
judges, each venture's three judges drawn at random, and their scores,
simulated so that the judges' disagreement and halo resemble those measured on
2019. Only rounded aggregates of 2019 enter; no record does."""

import numpy as np

CRITERIA = ("concept", "business_model", "market", "written_work", "investor_interest")


def run(inputs: dict, settings: dict) -> dict:
    rng = np.random.default_rng(inputs["seed"])
    n, j, k = settings["entries"], settings["judges"], settings["judges_per_entry"]
    p = settings["probabilities"]

    ventures = []
    for i in range(n):
        quality = float(rng.normal())
        writing = float(0.5 * quality + np.sqrt(0.75) * rng.normal())
        products = [x for x, pr in p["product_types"].items() if rng.random() < pr] or [max(p["product_types"], key=p["product_types"].get)]
        fields = [x for x, pr in p["fields"].items() if rng.random() < pr] or [max(p["fields"], key=p["fields"].get)]
        milestones = [x for x, pr in p["milestones"].items() if rng.random() < pr]
        entity = bool(rng.random() < p["entity_formed"])
        ventures.append({
            "venture": i + 1, "quality": quality, "writing": writing,
            "company_type": settings["company_types"][0] if rng.random() < p["internet_company"] else settings["company_types"][1],
            "product_types": products, "fields": fields, "milestones": milestones, "entity_formed": entity,
            "entity_type": str(rng.choice(settings["entity_types"])) if entity else None,
            "has_website": bool(rng.random() < p["website"]),
        })

    judges = [{"judge": i + 1, "persona": settings["personas"][i % len(settings["personas"])]} for i in range(j)]
    severity = rng.normal(size=j)
    jitter = rng.normal(size=(j, len(CRITERIA)))
    unique = rng.normal(size=(n, len(CRITERIA)))
    evaluations = []
    for v in ventures:
        for judge in sorted(rng.choice(j, size=k, replace=False)):
            impression, own = rng.normal(), rng.normal(size=len(CRITERIA))
            scores = {}
            for c_i, c in enumerate(CRITERIA):
                spec = settings["criteria"][c]
                base = v["writing"] if c == "written_work" else v["quality"]
                entry = np.sqrt(spec["entry"]) * spec["sd"] * (0.85 * base + 0.53 * unique[v["venture"] - 1, c_i])
                judge_part = np.sqrt(spec["judge"]) * spec["sd"] * (0.9 * severity[judge] + 0.44 * jitter[judge, c_i])
                residual = np.sqrt(1 - spec["entry"] - spec["judge"]) * spec["sd"] * (settings["halo"] * impression
                                                                                       + np.sqrt(1 - settings["halo"] ** 2) * own[c_i])
                scores[c] = int(np.clip(np.rint(spec["mean"] + entry + judge_part + residual), 1, 10))
            weighted = sum(settings["weights"][c] * scores[c] for c in CRITERIA)
            evaluations.append({"venture": v["venture"], "judge": int(judge) + 1, **scores, "weighted": round(weighted, 6)})

    means = {}
    for e in evaluations:
        means.setdefault(e["venture"], []).append(e["weighted"])
    order = sorted(means, key=lambda x: (-np.mean(means[x]), x))
    advanced = sorted(order[:int(round(settings["advance_share"] * n))])
    return {"ventures": ventures, "judges": judges, "evaluations": evaluations, "advanced": advanced}
