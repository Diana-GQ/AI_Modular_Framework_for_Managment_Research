"""Whether the embedders find the same topics: the adjusted Rand index between
each pair of embedders' topic assignments (Hubert & Arabie 1985)."""

from collections import Counter
from math import comb


def adjusted_rand(a: list, b: list) -> float:
    n = len(a)
    pairs = Counter(zip(a, b))
    sum_ij = sum(comb(v, 2) for v in pairs.values())
    sum_a = sum(comb(v, 2) for v in Counter(a).values())
    sum_b = sum(comb(v, 2) for v in Counter(b).values())
    expected = sum_a * sum_b / comb(n, 2)
    maximum = (sum_a + sum_b) / 2
    return (sum_ij - expected) / (maximum - expected) if maximum != expected else 1.0


def run(inputs: dict, settings: dict) -> dict:
    by = {}
    for row in inputs["assignments"]:
        by.setdefault(row["embedder"], {})[row["entry"]] = row["topic"]
    names = sorted(by)
    entries = sorted(set.intersection(*(set(v) for v in by.values())))
    out = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            out[f"{a}~{b}"] = adjusted_rand([by[a][e] for e in entries], [by[b][e] for e in entries])
    return {"adjusted_rand": out, "entries": len(entries)}
