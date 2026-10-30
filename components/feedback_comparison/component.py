"""Plan task 4.4, analysis A4 through embeddings (design, Section 4), for one
embedder: whether the AI judges' feedback discusses the same issues as the
human judges' on the same entry and question; whether AI feedback is more
alike across entries than human feedback; and whether feedback fits its own
summary better than the others.

Feedback lengths differ widely between sources, and length moves embeddings.
So "same issues" is measured as specificity: the mean similarity of two texts
on the same entry minus that of the same two sources' texts on different
entries. Similarities are cosine similarities of normalized vectors."""

import numpy as np
import pandas as pd

from pipeline.hashing import sha256_file
from pipeline.store import resolve


def load(ref: dict, ids: list) -> tuple[np.ndarray, dict]:
    path = resolve(ref)
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("a matrix does not match its SHA-256")
    return np.load(path, allow_pickle=False), {i: k for k, i in enumerate(ids)}


def pair_means(va, vb, ea, eb, same_source: bool) -> dict:
    if not len(va) or not len(vb):
        return {"same_entry": None, "different_entries": None, "specificity": None, "same_entry_pairs": 0}
    sim = va @ vb.T
    same = ea[:, None] == eb[None, :]
    valid = ~np.eye(len(va), dtype=bool) if same_source else np.ones_like(same)
    s, d = sim[same & valid], sim[~same & valid]
    return {"same_entry": float(s.mean()) if s.size else None, "different_entries": float(d.mean()) if d.size else None,
            "specificity": float(s.mean() - d.mean()) if s.size else None, "same_entry_pairs": int(s.size)}


def run(inputs: dict, settings: dict) -> dict:
    fb = pd.DataFrame(inputs["feedback"])
    vectors, index = load(inputs["feedback_vectors"], inputs["feedback_ids"])
    summaries, s_index = load(inputs["summary_vectors"], inputs["summary_ids"])
    entries = sorted(set(fb.loc[fb["source"] != "human", "entry"]))
    fb = fb[fb["entry"].isin(entries)].assign(row=lambda d: d["id"].map(index))
    s_rows = np.array([s_index[f"{e}|summary"] for e in entries])
    s_mat = summaries[s_rows]
    position = {e: k for k, e in enumerate(entries)}
    sources = [x for x in settings["sources"] if (fb["source"] == x).any()]
    out = {"entries": len(entries), "same_issues": {}, "alike_across_entries": {}, "fit_to_summary": {}, "words": {}}
    for q in [*settings["questions"], "all"]:
        d = fb if q == "all" else fb[fb["question"] == q]
        if q == "all":
            # Pairs only within a question: the question is part of what "same issues" means.
            groups = [fb[fb["question"] == x] for x in settings["questions"]]
        else:
            groups = [d]
        pairs = {}
        for a in sources:
            for b in sources[sources.index(a):]:
                parts = []
                for g in groups:
                    ga, gb = g[g["source"] == a], g[g["source"] == b]
                    parts.append(pair_means(vectors[ga["row"].to_numpy()], vectors[gb["row"].to_numpy()],
                                            ga["entry"].to_numpy(), gb["entry"].to_numpy(), a == b))
                key = f"{a}~{b}"
                pairs[key] = {k: (float(np.mean(v)) if (v := [p[k] for p in parts if p[k] is not None]) else None)
                              for k in ("same_entry", "different_entries", "specificity")}
                pairs[key]["same_entry_pairs"] = sum(p["same_entry_pairs"] for p in parts)
        out["same_issues"][q] = pairs
        out["alike_across_entries"][q] = {s: pairs[f"{s}~{s}"]["different_entries"] for s in sources}
        fit = {}
        for s in sources:
            ds = d[d["source"] == s]
            if ds.empty:
                fit[s] = None
                continue
            sim = vectors[ds["row"].to_numpy()] @ s_mat.T
            own = np.array([position[e] for e in ds["entry"]], dtype=int)
            own_sim = sim[np.arange(len(ds)), own]
            others = (sim.sum(axis=1) - own_sim) / (sim.shape[1] - 1)
            rank = (sim > own_sim[:, None]).sum(axis=1) + 1
            fit[s] = {"texts": int(len(ds)), "own_minus_others": float((own_sim - others).mean()),
                      "own_ranked_first": float((rank == 1).mean()), "mean_rank_of_own": float(rank.mean())}
        out["fit_to_summary"][q] = fit
        out["words"][q] = {s: (float(d.loc[d["source"] == s, "words"].mean()) if (d["source"] == s).any() else None)
                           for s in sources}
    return out
