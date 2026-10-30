"""Whether embedding similarity tracks what the ventures are about, checked
against the teams' own categories on the application form (known groups),
since no human ratings of similarity are available (design, Section 3).

For each embedder: the mean similarity of pairs whose teams chose at least two
of the same fields, against pairs with no field and no type of product in
common, with a 95% interval from resampling summaries; and the Spearman
correlation of similarity with the overlap of the teams' categories."""

import re

import numpy as np
from scipy import stats as sps

from components.shared import vectors


def options(value) -> set:
    return {p.strip() for p in re.split(r"\s*\|\s*", value) if p.strip()} if isinstance(value, str) else set()


def run(inputs: dict, settings: dict) -> dict:
    cats = {r["entry"]: (options(r["fields"]), options(r["product_type"])) for r in inputs["categories"]}
    entries = sorted(cats)
    n = len(entries)
    same = np.zeros((n, n), dtype=bool)
    none = np.zeros((n, n), dtype=bool)
    overlap = np.zeros((n, n))
    for i, a in enumerate(entries):
        for j, b in enumerate(entries):
            fa, pa = cats[a]
            fb, pb = cats[b]
            shared = len(fa & fb)
            same[i, j] = shared >= settings["same_fields_min"]
            none[i, j] = shared == 0 and not pa & pb
            union = (fa | pa) | (fb | pb)
            overlap[i, j] = len((fa | pa) & (fb | pb)) / len(union) if union else 0.0
    upper = np.triu(np.ones((n, n), dtype=bool), k=1)
    rng = np.random.default_rng(settings["seed"])
    samples = [rng.choice(n, size=n, replace=True) for _ in range(settings["bootstrap_reps"])]
    out = {}
    for row in inputs["matrices"]:
        s_all = vectors.load(row)
        index = {i.split("|")[0]: k for k, i in enumerate(row["ids"])}
        rows_ = np.array([index[e] for e in entries])
        sim = s_all[np.ix_(rows_, rows_)]
        diff = sim[same & upper].mean() - sim[none & upper].mean()
        pooled = np.sqrt((sim[same & upper].var(ddof=1) + sim[none & upper].var(ddof=1)) / 2)
        boot = []
        for idx in samples:
            s, g1, g0 = sim[np.ix_(idx, idx)], same[np.ix_(idx, idx)], none[np.ix_(idx, idx)]
            distinct = idx[:, None] != idx[None, :]
            m = np.triu(distinct, k=1)
            if (g1 & m).any() and (g0 & m).any():
                boot.append(s[g1 & m].mean() - s[g0 & m].mean())
        low, high = np.percentile(boot, [2.5, 97.5])
        out[row["embedder"]] = {
            "pairs_same_fields": int((same & upper).sum()), "pairs_nothing_in_common": int((none & upper).sum()),
            "mean_similarity_same_fields": float(sim[same & upper].mean()),
            "mean_similarity_nothing_in_common": float(sim[none & upper].mean()),
            "difference": float(diff), "standardized_difference": float(diff / pooled),
            "low": float(low), "high": float(high), "passed": bool(low > 0),
            "spearman_with_category_overlap": float(sps.spearmanr(sim[upper], overlap[upper])[0]),
        }
    return {"by_embedder": out, "summaries": n}
