"""Plan task 4.2, analysis A1: how closely an AI judge's scores agree with the
human judges', against the benchmark of how closely one human judge agrees
with the other two; how consistent the AI is across its five runs; and halo,
the correlation among an evaluator's five scores."""

import numpy as np
import pandas as pd

from components.shared import stats


def by_entry(df: pd.DataFrame, key: str) -> pd.DataFrame:
    return df.pivot_table(index="entry", columns=key, values="score", aggfunc="first")


def pooled_vs_other_two(human: pd.DataFrame, other, entries) -> tuple[list, list, list]:
    """For each entry and each of its three judges held out: the held-out
    judge's score, the mean of the other two, and `other`'s value for the entry."""
    held, rest, alt = [], [], []
    for entry, rows in human[human["entry"].isin(entries)].groupby("entry", sort=True):
        values = rows.sort_values("judge")["score"].to_numpy(dtype=float)
        for i in range(len(values)):
            held.append(values[i])
            rest.append(np.delete(values, i).mean())
            alt.append(other[entry])
    return held, rest, alt


def bootstrap_difference(human, ai_mean, entries, reps, seed) -> dict:
    """95% interval for r(AI, other two) − r(one judge, other two), resampling entries."""
    rng = np.random.default_rng(seed)
    groups = {e: rows.sort_values("judge")["score"].to_numpy(dtype=float)
              for e, rows in human[human["entry"].isin(entries)].groupby("entry", sort=True)}
    keys = sorted(groups)
    diffs = []
    for _ in range(reps):
        sample = rng.choice(len(keys), size=len(keys), replace=True)
        held, rest, alt = [], [], []
        for idx in sample:
            values = groups[keys[idx]]
            for i in range(len(values)):
                held.append(values[i])
                rest.append(np.delete(values, i).mean())
                alt.append(ai_mean[keys[idx]])
        diffs.append(np.corrcoef(alt, rest)[0, 1] - np.corrcoef(held, rest)[0, 1])
    low, high = np.percentile(diffs, [2.5, 97.5])
    return {"low": float(low), "high": float(high), "reps": reps}


def run(inputs: dict, settings: dict) -> dict:
    human = pd.DataFrame(inputs["human"])
    ai = pd.DataFrame(inputs["ai"])
    names = {**settings["criteria"], "weighted": "weighted_score"}
    entries = sorted(set(ai["entry"]) & set(human["entry"]))
    out = {}
    for question, name in names.items():
        h = human[human["question"] == question]
        a = ai[ai["question"] == question]
        h_mean = h.groupby("entry")["score"].mean().reindex(entries)
        runs = by_entry(a, "run").reindex(entries)
        a_mean = runs.mean(axis=1)
        held, rest, alt = pooled_vs_other_two(h, a_mean, entries)
        _, _, alt_run1 = pooled_vs_other_two(h, runs[1], entries)
        identical = (runs.nunique(axis=1) == 1)
        out[name] = {
            "entries": len(entries),
            "human_mean": float(h_mean.mean()), "ai_mean": float(a_mean.mean()),
            "mean_difference": float((a_mean - h_mean).mean()),
            "sd_entry_means": {"human": float(h_mean.std(ddof=1)), "ai": float(a_mean.std(ddof=1))},
            "ai_vs_human_mean": stats.correlations(a_mean, h_mean),
            "vs_other_two": {
                "one_judge": stats.correlations(held, rest),
                "ai_mean_of_runs": stats.correlations(alt, rest),
                "ai_one_run": stats.correlations(alt_run1, rest),
                "difference_ai_mean_minus_one_judge": bootstrap_difference(
                    h, a_mean, entries, settings["bootstrap_reps"], settings["seed"]),
            },
            "run_consistency": {**stats.icc1(runs.to_numpy()),
                                "share_identical_across_runs": float(identical.mean()),
                                "mean_sd_within_entry": float(runs.std(axis=1, ddof=1).mean())},
        }
        out[name]["vs_other_two"]["difference_ai_mean_minus_one_judge"]["estimate"] = (
            out[name]["vs_other_two"]["ai_mean_of_runs"]["pearson"] - out[name]["vs_other_two"]["one_judge"]["pearson"])

    # Halo: the correlations among an evaluator's five scores.
    crit = list(settings["criteria"])
    h_eval = human[human["question"].isin(crit)].pivot_table(index=["entry", "judge"], columns="question", values="score")[crit]
    a_eval = ai[ai["question"].isin(crit)].pivot_table(index=["entry", "run"], columns="question", values="score")[crit]
    h_ent = human[human["question"].isin(crit) & human["entry"].isin(entries)].pivot_table(
        index="entry", columns="question", values="score", aggfunc="mean")[crit]
    a_ent = ai[ai["question"].isin(crit)].pivot_table(index="entry", columns="question", values="score", aggfunc="mean")[crit].reindex(h_ent.index)

    def halo(frame):
        corr = frame.corr().to_numpy()
        return {"mean_correlation": stats.mean_offdiagonal(corr), "first_eigenvalue_share": stats.first_eigenvalue_share(corr),
                "observations": int(len(frame))}

    cross = pd.concat([h_ent.add_prefix("human_"), a_ent.add_prefix("ai_")], axis=1).corr()
    convergent = [cross.loc[f"ai_{c}", f"human_{c}"] for c in crit]
    hetero_hetero = [cross.loc[f"ai_{c}", f"human_{d}"] for c in crit for d in crit if c != d]
    out_halo = {
        "one_evaluation": {"human": halo(h_eval), "ai_one_run": halo(a_eval)},
        "entry_means": {"human_mean_of_judges": halo(h_ent), "ai_mean_of_runs": halo(a_ent)},
        "multitrait_multimethod": {
            "same_criterion_across_methods": float(np.mean(convergent)),
            "different_criteria_across_methods": float(np.mean(hetero_hetero)),
            "different_criteria_within_human": halo(h_ent)["mean_correlation"],
            "different_criteria_within_ai": halo(a_ent)["mean_correlation"],
            "same_criterion_by_criterion": {settings["criteria"][c]: float(v) for c, v in zip(crit, convergent)},
        },
    }
    return {"by_criterion": out, "halo": out_halo}
