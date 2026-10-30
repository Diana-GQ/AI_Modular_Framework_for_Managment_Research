"""Plan task 5.3, analysis A5 (design, Section 4): which features of the
summaries (form) and of the ventures (substance) explain the human judges'
scores, the AI judges' scores, where they diverge, and who advanced.

Outcomes are standardized; continuous features are standardized and binary
ones left as 0 or 1. OLS with HC3 standard errors; the share of variance each
group of features explains, with bootstrap intervals for comparing form with
substance and humans with AI. Exploratory: one year, 134 entries."""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def r2(y: np.ndarray, x: np.ndarray) -> float:
    x1 = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(x1, y, rcond=None)
    resid = y - x1 @ beta
    return float(1 - resid @ resid / ((y - y.mean()) @ (y - y.mean())))


def prepare(features: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    x = features[columns].astype(float)
    for c in columns:
        if set(x[c].dropna().unique()) - {0.0, 1.0}:
            x[c] = (x[c] - x[c].mean()) / x[c].std(ddof=1)
    return x


def run(inputs: dict, settings: dict) -> dict:
    outcomes = pd.DataFrame(inputs["outcomes"]).set_index("entry")
    features = pd.DataFrame(inputs["features"]).set_index("entry")
    df = outcomes.join(features, how="inner").dropna(subset=settings["form"] + settings["substance"])
    z = lambda s: (s - s.mean()) / s.std(ddof=1)
    ys = {"human": z(df["human"]), "claude": z(df["claude"]), "qwen": z(df["qwen"])}
    ys["divergence_claude"] = ys["claude"] - ys["human"]
    ys["divergence_qwen"] = ys["qwen"] - ys["human"]
    form, substance = prepare(df, settings["form"]), prepare(df, settings["substance"])
    both = pd.concat([form, substance], axis=1)
    groups = {"form": form, "substance": substance, "both": both}

    explained, coefficients = {}, {}
    for name, y in ys.items():
        explained[name] = {g: r2(y.to_numpy(), x.to_numpy()) for g, x in groups.items()}
        fit = sm.OLS(y.to_numpy(), sm.add_constant(both.to_numpy())).fit(cov_type="HC3")
        ci = fit.conf_int()
        coefficients[name] = {c: {"coefficient": float(fit.params[i + 1]), "low": float(ci[i + 1][0]),
                                  "high": float(ci[i + 1][1]), "p": float(fit.pvalues[i + 1])}
                              for i, c in enumerate(both.columns)}
        explained[name]["adjusted_both"] = float(fit.rsquared_adj)

    rng = np.random.default_rng(settings["seed"])
    n = len(df)
    comparisons = {"form_minus_substance": {k: [] for k in ys}, "claude_minus_human": {"form": [], "substance": [], "both": []}}
    for _ in range(settings["bootstrap_reps"]):
        idx = rng.choice(n, size=n, replace=True)
        values = {k: {g: r2(y.to_numpy()[idx], x.to_numpy()[idx]) for g, x in groups.items()} for k, y in ys.items()}
        for k in ys:
            comparisons["form_minus_substance"][k].append(values[k]["form"] - values[k]["substance"])
        for g in groups:
            comparisons["claude_minus_human"][g].append(values["claude"][g] - values["human"][g])
    intervals = {c: {k: {"low": float(np.percentile(v, 2.5)), "high": float(np.percentile(v, 97.5))} for k, v in d.items()}
                 for c, d in comparisons.items()}

    # Advancement: who advanced, against the human score and the features.
    adv = df["advanced"].astype(float)
    descriptive = {c: {"advanced": float(df.loc[adv == 1, c].astype(float).mean()), "not_advanced": float(df.loc[adv == 0, c].astype(float).mean())}
                   for c in settings["form"] + settings["substance"]}
    x_adv = pd.concat([ys["human"].rename("human_score"), both], axis=1)
    fit = sm.OLS(adv.to_numpy(), sm.add_constant(x_adv.to_numpy())).fit(cov_type="HC3")
    ci = fit.conf_int()
    lpm = {c: {"coefficient": float(fit.params[i + 1]), "low": float(ci[i + 1][0]), "high": float(ci[i + 1][1]), "p": float(fit.pvalues[i + 1])}
           for i, c in enumerate(x_adv.columns)}
    beyond = {}
    for judge in ("claude", "qwen"):
        x2 = pd.concat([ys["human"].rename("human_score"), ys[judge].rename(f"{judge}_score")], axis=1)
        f2 = sm.OLS(adv.to_numpy(), sm.add_constant(x2.to_numpy())).fit(cov_type="HC3")
        c2 = f2.conf_int()
        beyond[judge] = {c: {"coefficient": float(f2.params[i + 1]), "low": float(c2[i + 1][0]), "high": float(c2[i + 1][1])}
                         for i, c in enumerate(x2.columns)}
    return {"entries": int(n), "explained": explained, "intervals": intervals, "coefficients": coefficients,
            "advancement": {"advanced": int(adv.sum()), "means": descriptive, "linear_probability": lpm,
                            "ai_score_beyond_human_score": beyond}}
