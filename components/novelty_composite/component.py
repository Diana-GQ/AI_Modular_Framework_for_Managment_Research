"""The primary novelty measure (design, Section 3): the mean of the three
embedders' novelty scores, each standardized over the year's summaries. A
composite of measures that agree only partly is more reliable than any one of
them, as the mean of several raters is."""

import numpy as np
import pandas as pd


def run(inputs: dict, settings: dict) -> dict:
    df = pd.DataFrame(inputs["scores"]).pivot(index="entry", columns="embedder", values="novelty")
    if sorted(df.columns) != sorted(settings["embedders"]):
        raise ValueError("expected one novelty score per embedder")
    z = (df - df.mean()) / df.std(ddof=1)
    composite = z.mean(axis=1)
    corr = df.corr(method="spearman")
    pairs = [corr.loc[a, b] for i, a in enumerate(sorted(df.columns)) for b in sorted(df.columns)[i + 1:]]
    k, r = len(df.columns), float(np.mean(pairs))
    return {"composite": [{"entry": e, "novelty": float(v)} for e, v in composite.sort_index().items()],
            "agreement": {"mean_spearman_between_embedders": r,
                          "spearman_brown_reliability": k * r / (1 + (k - 1) * r)}}
