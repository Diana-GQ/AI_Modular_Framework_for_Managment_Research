"""Whether the embedders see the same structure (design, Section 3): the
Spearman correlation between two embedders' pairwise similarities over the
same texts (representational similarity analysis; Kriegeskorte, Mur &
Bandettini 2008). Comparing similarity structures, not vectors, is allowed
across vector types."""

import numpy as np
from scipy import stats as sps

from pipeline.hashing import sha256_file
from pipeline.store import resolve


def run(inputs: dict, settings: dict) -> dict:
    mats = {}
    for row in inputs["matrices"]:
        path = resolve(row)
        if sha256_file(path) != row["sha256"]:
            raise ValueError("a matrix does not match its SHA-256")
        mats[row["embedder"]] = (np.load(path, allow_pickle=False), list(row["ids"]))
    names = sorted(mats)
    ids = mats[names[0]][1]
    if any(mats[n][1] != ids for n in names):
        raise ValueError("the matrices must embed the same texts in the same order")
    rng = np.random.default_rng(settings["seed"])
    sample = np.sort(rng.choice(len(ids), size=min(settings["sample_size"], len(ids)), replace=False))
    upper = np.triu_indices(len(sample), k=1)
    sims = {n: (mats[n][0][sample] @ mats[n][0][sample].T)[upper] for n in names}
    out = {"texts": len(ids), "sampled": int(len(sample)), "pairs": int(len(upper[0])), "spearman": {}}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            out["spearman"][f"{a}~{b}"] = float(sps.spearmanr(sims[a], sims[b])[0])
    return {"agreement": out}
