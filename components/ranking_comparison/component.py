"""Plan task 4.3, analyses A2 and A3 (design, Section 4).

A2: rank the entries by an AI judge's weighted score (mean of its five runs)
and by the human judges' (mean of three); let the AI select as many entries as
advanced, and measure the overlap; list who would gain and who would lose.

A3: test the expectations that human and AI judges agree on the strongest
entries and diverge near the advancement cutoff, beyond the human judges' own
disagreement at the same positions. Each judge of an entry is held out in
turn; the mean of the other two ranks the entries (the reference). At each
reference position, the AI's rank difference from the reference is compared
with the held-out judge's. Intervals come from resampling entries."""

import numpy as np
import pandas as pd
from scipy import stats as sps


def ranks(values: pd.Series) -> pd.Series:
    """1 is the best; ties share the average rank."""
    return pd.Series(sps.rankdata(-values.to_numpy(dtype=float), method="average"), index=values.index)


def select(values: pd.Series, n: int) -> set:
    """The top n, ties broken by entry code so that the selection is reproducible."""
    order = sorted(values.index, key=lambda e: (-values[e], e))
    return set(order[:n])


def overlap(a: set, b: set) -> dict:
    return {"overlap": len(a & b), "jaccard": len(a & b) / len(a | b) if a | b else None}


def run(inputs: dict, settings: dict) -> dict:
    human = pd.DataFrame(inputs["human"])
    ai = pd.DataFrame(inputs["ai"])
    advanced = pd.DataFrame(inputs["advanced"]).set_index("entry")["advanced"]
    entries = sorted(set(ai["entry"]) & set(human["entry"]))
    h_mean = human.groupby("entry")["score"].mean().reindex(entries)
    ai_runs = ai.pivot_table(index="entry", columns="run", values="score").reindex(entries)
    ai_mean = ai_runs.mean(axis=1)
    adv = advanced.reindex(entries).fillna(False).astype(bool)
    n = int(adv.sum())

    # A2: rankings and selections.
    ai_sel, h_sel, adv_set = select(ai_mean, n), select(h_mean, n), set(adv[adv].index)
    h_rank = ranks(h_mean)
    cutoff_score = sorted(ai_mean, reverse=True)[n - 1]
    a2 = {
        "entries": len(entries), "selected": n,
        "rank_correlation": {"spearman": float(sps.spearmanr(ai_mean, h_mean)[0]),
                             "kendall_tau_b": float(sps.kendalltau(ai_mean, h_mean)[0])},
        "ai_selection_vs_advanced": overlap(ai_sel, adv_set),
        "ai_selection_vs_human_top": overlap(ai_sel, h_sel),
        "human_top_vs_advanced": overlap(h_sel, adv_set),
        "entries_tied_at_the_ai_cutoff": int((ai_mean == cutoff_score).sum()),
        "would_gain": sorted(ai_sel - adv_set),
        "would_lose": sorted(adv_set - ai_sel),
        "human_rank_of_those_who_would_gain": sorted(float(h_rank[e]) for e in ai_sel - adv_set),
        "human_rank_of_those_who_would_lose": sorted(float(h_rank[e]) for e in adv_set - ai_sel),
    }

    # A3: disagreement with the reference (mean of two judges) by reference position.
    top, half = settings["top_band"], settings["cutoff_half_width"]
    rows = []
    for position in range(settings["judges_per_entry"]):
        held, rest = {}, {}
        for entry, g in human[human["entry"].isin(entries)].groupby("entry", sort=True):
            values = g.sort_values("judge")["score"].to_numpy(dtype=float)
            held[entry], rest[entry] = values[position], np.delete(values, position).mean()
        held, rest = pd.Series(held).reindex(entries), pd.Series(rest).reindex(entries)
        r_ref, r_held = ranks(rest), ranks(held)
        r_ai, r_ai1 = ranks(ai_mean), ranks(ai_runs[1])
        for e in entries:
            rows.append({"entry": e, "position": position, "ref": r_ref[e],
                         "d_judge": abs(r_held[e] - r_ref[e]), "d_ai": abs(r_ai[e] - r_ref[e]),
                         "d_ai_one_run": abs(r_ai1[e] - r_ref[e]),
                         "flip_judge": (r_held[e] <= n) != (r_ref[e] <= n), "flip_ai": (r_ai[e] <= n) != (r_ref[e] <= n),
                         "flip_ai_one_run": (r_ai1[e] <= n) != (r_ref[e] <= n)})
    d = pd.DataFrame(rows)
    bands = {"strongest": d["ref"] <= top, "cutoff": (d["ref"] - n).abs() <= half}
    rng = np.random.default_rng(settings["seed"])
    by_entry = {e: g.index.to_numpy() for e, g in d.groupby("entry")}
    keys = sorted(by_entry)
    samples = [np.concatenate([by_entry[keys[i]] for i in rng.choice(len(keys), len(keys), replace=True)])
               for _ in range(settings["bootstrap_reps"])]

    def compare(mask, ai_col, judge_col):
        est = float(d.loc[mask, ai_col].mean() - d.loc[mask, judge_col].mean())
        boot = []
        for idx in samples:
            sub = d.loc[idx]
            m = mask.loc[idx].to_numpy()
            if m.any():
                boot.append(sub.loc[m, ai_col].mean() - sub.loc[m, judge_col].mean())
        low, high = np.percentile(boot, [2.5, 97.5])
        return {"ai": float(d.loc[mask, ai_col].mean()), "judge": float(d.loc[mask, judge_col].mean()),
                "difference": est, "low": float(low), "high": float(high)}

    a3 = {"reference": "mean of two judges, each judge of an entry held out in turn",
          "bands": {"strongest": f"reference rank 1 to {top}", "cutoff": f"reference rank {n - half} to {n + half}"},
          "pairs": {k: int(v.sum()) for k, v in bands.items()}}
    for band, mask in bands.items():
        a3[band] = {
            "mean_absolute_rank_difference": compare(mask, "d_ai", "d_judge"),
            "mean_absolute_rank_difference_one_run": compare(mask, "d_ai_one_run", "d_judge"),
            "share_on_the_other_side_of_the_cutoff": compare(mask, "flip_ai", "flip_judge"),
        }
    return {"rankings_and_selection": a2, "expectations": a3}
