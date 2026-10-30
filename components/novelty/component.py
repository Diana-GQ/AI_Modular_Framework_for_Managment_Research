"""Plan task 5.1: novelty as distinctiveness from the year's other summaries
(design, Section 3), from one embedder's normalized vectors: one minus the mean
cosine similarity to the k most similar summaries of the year, and, beside it,
one minus the similarity to the centroid of the others. Also stores the
similarity matrix, which the coders' similarity ratings validate.

Among the variants compared on the 2019 summaries (centring, whitening to 8 to
64 components, nearest neighbours or all summaries or the centroid), the k
nearest neighbours on the normalized vectors agreed best across the three
embedders; no outcome entered the comparison."""

import numpy as np

from components.shared import vectors


def run(inputs: dict, settings: dict) -> dict:
    x = vectors.load(inputs["vectors"])
    ids = inputs["ids"]
    w = x / np.linalg.norm(x, axis=1, keepdims=True)
    sim = w @ w.T
    n, k = len(ids), settings["nearest_neighbours"]
    masked = sim - 2 * np.eye(n)
    nearest = np.sort(masked, axis=1)[:, -k:].mean(axis=1)
    others = (w.sum(axis=0)[None, :] - w) / (n - 1)
    centroid = (w * others).sum(axis=1) / np.linalg.norm(others, axis=1)
    scores = [{"entry": i.split("|")[0], "novelty": float(1 - a), "novelty_centroid": float(1 - b)}
              for i, a, b in zip(ids, nearest, centroid)]
    return {"scores": scores, "similarity": vectors.put_matrix(sim), "ids": list(ids)}
