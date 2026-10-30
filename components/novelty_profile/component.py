"""A description, not a test: the human and AI scores and the share advanced in
each fifth of the entries by novelty. Novelty has no human validation in this
study, so it does not enter inference (proposal, Section 4.4); this table only
shows the pattern, for the optimal-distinctiveness question of A5."""

import numpy as np
import pandas as pd


def run(inputs: dict, settings: dict) -> dict:
    df = pd.DataFrame(inputs["outcomes"]).set_index("entry").join(
        pd.DataFrame(inputs["novelty"]).set_index("entry"), how="inner")
    df = df.sort_values("novelty")
    bins = np.array_split(np.arange(len(df)), settings["bins"])
    rows = []
    for k, idx in enumerate(bins, 1):
        part = df.iloc[idx]
        rows.append({"bin": k, "entries": int(len(part)), "novelty_low": float(part["novelty"].min()),
                     "novelty_high": float(part["novelty"].max()), "human": float(part["human"].mean()),
                     "claude": float(part["claude"].mean()), "qwen": float(part["qwen"].mean()),
                     "share_advanced": float(part["advanced"].astype(float).mean())})
    return {"by_bin": rows, "note": "description only; novelty is not validated, so no test is run"}
