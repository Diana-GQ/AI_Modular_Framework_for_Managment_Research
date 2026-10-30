"""The open-weight judge's client: the requests sent to its deployment on Modal
(pipeline/modal_qwen.py), and the reading of its results."""

import json


def qwen_request(*, system: str, document_part: str, question_part: str, max_tokens: int, sampling: dict,
                 seed: int, structured: dict | None) -> dict:
    """A request for the open-weight judge, in chat form, with its own seed.
    `structured` is the decoding constraint (vLLM's structured-output options),
    or None for plain text."""
    return {
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": document_part + question_part}],
        "sampling": dict(sampling, max_tokens=max_tokens, seed=seed),
        "structured_outputs": structured,
    }


def parse_qwen(result: dict, kind: str) -> dict:
    """Status and parsed answer of one open-weight result, named as for Claude.
    A written answer is plain text; a score answer is a JSON object."""
    record = {"parsed": None, "model_served": result.get("model")}
    if result.get("finish_reason") != "stop":
        record["status"] = "max_tokens" if result.get("finish_reason") == "length" else "other"
        return record
    text = (result.get("text") or "").strip()
    try:
        record["parsed"] = {"response": text} if kind == "written" else json.loads(text)
        record["status"] = "ok" if text else "unparseable"
    except json.JSONDecodeError:
        record["status"] = "unparseable"
    return record
