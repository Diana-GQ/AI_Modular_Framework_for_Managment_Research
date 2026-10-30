"""Plan task 4.1: how much the human judges agree, the benchmark for Study A.

For each criterion and for the weighted score: intraclass correlations; the
variance of the scores divided, by a model with crossed random effects for
entries and judges, into differences between entries, each judge's overall
severity (level noise) and each judge's reactions to particular entries
(pattern noise, together with any other error); and how closely one judge
agrees with the other two."""

import warnings

import numpy as np
import pandas as pd

from components.shared import stats


def _reml(df: pd.DataFrame, effects: list[str]):
    """REML fit of score = mean + the given crossed random effects + residual.
    Near a variance of zero the likelihood is flat, and a gradient search can stop
    at the boundary short of the best fit. So Powell's derivative-free search goes
    first, and BFGS refines its result; the fit with the higher likelihood is kept."""
    import statsmodels.formula.api as smf

    model = smf.mixedlm("score ~ 1", df.assign(all=1), groups="all", re_formula="0",
                        vc_formula={e: f"0 + C({e})" for e in effects})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rough = model.fit(reml=True, method="powell")
        # A tolerance BFGS reliably reaches: a tighter one leaves it wandering where the likelihood is flat.
        fine = model.fit(reml=True, method="bfgs", start_params=rough.params_object, gtol=1e-6, maxiter=2000)
    fit = fine if fine.llf >= rough.llf else rough
    var = {name: float(v) for name, v in zip(model.exog_vc.names, fit.vcomp)}
    var["residual"] = float(fit.scale)
    return var, fit


def variance_components(df: pd.DataFrame) -> dict:
    """Score = mean + entry + judge + residual, entries and judges crossed. A
    variance estimated at essentially zero is set to zero, and the others are
    fitted again without it, so that the estimate does not wander along the boundary."""
    var, fit = _reml(df, ["entry", "judge"])
    total = sum(var.values())
    zero = [e for e in ("entry", "judge") if var[e] < 1e-6 * total]
    if zero:
        rest = [e for e in ("entry", "judge") if e not in zero]
        if rest:
            var, fit = _reml(df, rest)
        else:
            var = {"residual": float(df["score"].var(ddof=1))}
        var.update(dict.fromkeys(zero, 0.0))
    var = {k: var[k] for k in ("entry", "judge", "residual")}
    total = sum(var.values())
    no_effects = zero == ["entry", "judge"]
    return {"variance": var, "share": {k: v / total for k, v in var.items()},
            "converged": True if no_effects else bool(fit.converged),
            "mean": float(df["score"].mean()) if no_effects else float(fit.fe_params.iloc[0])}


def run(inputs: dict, settings: dict) -> dict:
    scores = pd.DataFrame(inputs["scores"])
    out = {}
    for question, name in {**settings["criteria"], "weighted": "weighted_score"}.items():
        df = scores[scores["question"] == question].sort_values(["entry", "judge"])
        per_entry = df.groupby("entry")["score"].apply(list)
        complete = per_entry[per_entry.map(len) == settings["judges_per_entry"]]
        icc = stats.icc1(np.vstack(complete.to_list()))
        vc = variance_components(df)
        v = vc["variance"]
        k = settings["judges_per_entry"]
        loo = stats.leave_one_out(df, "score")
        held, others = [x[2] for x in loo], [x[3] for x in loo]
        out[name] = {
            "evaluations": int(len(df)), "entries": int(df["entry"].nunique()), "judges": int(df["judge"].nunique()),
            "mean": float(df["score"].mean()), "sd": float(df["score"].std(ddof=1)),
            **icc,
            "variance": v, "share": vc["share"], "converged": vc["converged"],
            "reliability_one_judge": v["entry"] / (v["entry"] + v["judge"] + v["residual"]),
            f"reliability_mean_of_{k}": v["entry"] / (v["entry"] + (v["judge"] + v["residual"]) / k),
            "one_judge_vs_other_two": stats.correlations(held, others),
        }
    return {"by_criterion": out}
