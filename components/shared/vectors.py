"""What the content measures share: loading a matrix from the store, and the
centred, whitened, normalized vectors of one year's summaries (Su et al. 2021)."""

import io

import numpy as np

from pipeline.hashing import sha256_file
from pipeline.store import Store, resolve


def load(ref: dict) -> np.ndarray:
    path = resolve(ref)
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("a matrix does not match its SHA-256")
    return np.load(path, allow_pickle=False)


def whiten(x: np.ndarray, dimensions: int) -> tuple[np.ndarray, float]:
    """Centre on the year's mean, keep the leading principal components with unit
    variance each, and normalize. Returns the vectors and the share of variance kept."""
    centred = x - x.mean(axis=0, keepdims=True)
    u, s, _ = np.linalg.svd(centred, full_matrices=False)
    k = min(dimensions, len(s) - 1)
    w = u[:, :k] * np.sqrt(len(x))
    w /= np.linalg.norm(w, axis=1, keepdims=True)
    return w, float((s[:k] ** 2).sum() / (s ** 2).sum())


def put_matrix(matrix: np.ndarray) -> dict:
    buffer = io.BytesIO()
    np.save(buffer, np.asarray(matrix, dtype=np.float32), allow_pickle=False)
    return Store().put_file(buffer.getvalue(), ".npy")
