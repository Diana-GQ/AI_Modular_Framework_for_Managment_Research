"""Asks the open-weight judge (Qwen3-8B, served on Modal by pipeline/modal_qwen.py)
one question about one executive summary (design, Section 2).

Run r samples with seed r. Requests are sent in batches to a deployment that
lives only inside session(): it starts on the first batch, and Modal shuts it
down when the session ends. The deployment's pins must match the contract's."""

import contextlib
import time

from components.shared import judge
from pipeline import modal_qwen, models, qwen_client

_session: dict | None = None


def check_pins(settings: dict) -> None:
    model = settings["model"]
    deployed = {"id": modal_qwen.MODEL, "revision": modal_qwen.REVISION, "image": modal_qwen.IMAGE, "gpu": modal_qwen.GPU}
    differences = [k for k, v in deployed.items() if model.get(k) != v]
    if differences:
        raise models.ModelMismatch(f"the deployment differs from the contract in {', '.join(differences)}")


@contextlib.contextmanager
def session(settings: dict):
    """The deployment, for the duration of the block, with its environment recorded."""
    global _session
    check_pins(settings)
    started = time.time()
    with modal_qwen.app.run():
        judge_cls = modal_qwen.QwenJudge()
        _session = {"judge": judge_cls, "environment": judge_cls.environment.remote(), "started": started}
        try:
            yield _session
        finally:
            _session = None


def request(inputs: dict, settings: dict, prompts: dict | None = None) -> tuple[str, dict]:
    """Written answers are plain text; score answers are held to the contract's pattern."""
    kind, parts = judge.message_parts(prompts or judge.prompts(), inputs)
    parts.pop("schema")
    return kind, qwen_client.qwen_request(**parts, max_tokens=settings["max_tokens"][kind], sampling=settings["sampling"],
                                     seed=settings["seeds"][inputs["run"] - 1],
                                     structured=settings["structured_outputs"][kind])


def run_batch(batch: list[dict], settings: dict) -> list[dict]:
    if _session is None:
        with session(settings):
            return run_batch(batch, settings)
    prompts = judge.prompts()
    kinds, requests = zip(*(request(inputs, settings, prompts) for inputs in batch))
    started = time.time()
    results = _session["judge"].generate.remote(list(requests))
    seconds = time.time() - started
    out = []
    for kind, req, res in zip(kinds, requests, results):
        if (res["model"], res["revision"]) != (settings["model"]["id"], settings["model"]["revision"]):
            raise models.ModelMismatch(f"answered by {res['model']} at {res['revision']}")
        record = qwen_client.parse_qwen(res, kind)
        details = {"request": req, "response": res, "status": record["status"],
                   "environment": _session["environment"], "batch_size": len(batch), "batch_seconds": seconds}
        out.append(judge.outputs(record["status"], record["parsed"], kind, record["model_served"]) | {"_details": details})
    return out


def run(inputs: dict, settings: dict) -> dict:
    return run_batch([inputs], settings)[0]
