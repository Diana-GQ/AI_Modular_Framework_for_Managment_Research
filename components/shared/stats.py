"""Statistics shared by the validators of Study A (design, Section 4)."""

import numpy as np
from scipy import stats

CRITERIA = {"Q2": "concept", "Q4": "business_model", "Q6": "market", "Q7": "written_work", "Q9": "investor_interest"}


def icc1(matrix) -> dict:
    """One-way intraclass correlations for targets (rows) rated by k
    interchangeable raters or runs (columns): ICC(1) for one rating, and
    ICC(1,k) for the mean of the k ratings (Shrout & Fleiss 1979)."""
    m = np.asarray(matrix, dtype=float)
    n, k = m.shape
    grand, means = m.mean(), m.mean(axis=1)
    msb = k * ((means - grand) ** 2).sum() / (n - 1)
    msw = ((m - means[:, None]) ** 2).sum() / (n * (k - 1))
    single = (msb - msw) / (msb + (k - 1) * msw) if msb + (k - 1) * msw else float("nan")
    mean_k = (msb - msw) / msb if msb else float("nan")
    return {"icc1_single": float(single), "icc1_mean": float(mean_k), "k": k, "targets": n}


def correlations(x, y) -> dict:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    return {"pearson": float(stats.pearsonr(x, y)[0]), "spearman": float(stats.spearmanr(x, y)[0]), "n": int(len(x))}


def mean_offdiagonal(corr) -> float:
    c = np.asarray(corr, dtype=float)
    return float(c[~np.eye(len(c), dtype=bool)].mean())


def first_eigenvalue_share(corr) -> float:
    values = np.linalg.eigvalsh(np.asarray(corr, dtype=float))
    return float(values.max() / values.sum())


def leave_one_out(table, value) -> list[tuple]:
    """For entries with three ratings: each rating held out in turn against the
    mean of the other two, as (entry, held-out position, held-out value, mean
    of the other two). Positions follow the order of the rows within an entry."""
    out = []
    for entry, rows in table.groupby("entry", sort=True):
        values = rows[value].to_numpy(dtype=float)
        for i in range(len(values)):
            others = np.delete(values, i)
            out.append((entry, i, values[i], others.mean()))
    return out
