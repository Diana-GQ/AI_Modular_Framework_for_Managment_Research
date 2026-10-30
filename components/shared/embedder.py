"""What the embedders share (design, Section 3): sending texts to the
deployment on Modal (pipeline/modal_embed.py), one model per component, and
keeping the vectors in the store as one matrix, in the order of the texts."""

import io
import statistics
import time

import numpy as np

from pipeline import modal_embed
from pipeline.models import ModelMismatch
from pipeline.store import Store


def check_pins(settings: dict) -> None:
    model = settings["model"]
    if modal_embed.MODELS.get(model["id"]) != model["revision"] or model["gpu"] != modal_embed.GPU:
        raise ModelMismatch("the deployment differs from the contract in its model, revision or GPU")


def run(inputs: dict, settings: dict) -> dict:
    check_pins(settings)
    ids = [row["id"] for row in inputs["texts"]]
    texts = [row["text"] for row in inputs["texts"]]
    if len(set(ids)) != len(ids):
        raise ValueError("text ids must be unique")
    chunk = settings["texts_per_call"]
    parts, tokens = [], []
    started = time.time()
    with modal_embed.app.run():
        embedder = modal_embed.Embedder(model_id=settings["model"]["id"], revision=settings["model"]["revision"],
                                        dtype=settings["dtype"], max_seq_length=settings["max_seq_length"])
        environment = embedder.environment.remote()
        for i in range(0, len(texts), chunk):
            result = embedder.embed.remote(texts[i:i + chunk], settings["instruction"])
            parts.append(np.load(io.BytesIO(result["npy"]), allow_pickle=False))
            tokens += result["tokens"]
    matrix = np.vstack(parts).astype(np.float32)
    buffer = io.BytesIO()
    np.save(buffer, matrix, allow_pickle=False)
    return {
        "vectors": Store().put_file(buffer.getvalue(), ".npy"),
        "ids": ids,
        "dimension": int(matrix.shape[1]),
        "truncated": int(sum(t > settings["max_seq_length"] for t in tokens)),
        "_details": {"environment": environment, "seconds": round(time.time() - started, 1), "texts": len(texts),
                     "tokens": {"min": min(tokens), "median": statistics.median(tokens), "max": max(tokens)}},
    }
