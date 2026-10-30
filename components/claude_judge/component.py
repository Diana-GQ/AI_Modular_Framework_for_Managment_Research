"""Asks Claude one question about one executive summary (design, Section 2).

The summary's part of the message is marked for caching, so the ten questions
and five runs on a summary reuse it. A failed call (network, server) raises and
stores nothing; a refusal, or an answer cut off at the length limit, is stored
as the run's answer and counts as missing."""

import threading

from components.shared import judge
from pipeline import claude_client

_client = None
_lock = threading.Lock()


def client() -> claude_client.ClaudeClient:
    global _client
    with _lock:
        if _client is None:
            _client = claude_client.ClaudeClient()
    return _client


def request(inputs: dict, settings: dict, prompts: dict | None = None) -> tuple[str, dict]:
    kind, parts = judge.message_parts(prompts or judge.prompts(), inputs)
    return kind, claude_client.ClaudeClient.build_request(
        model=settings["model"]["id"], **parts, max_tokens=settings["max_tokens"][kind],
        effort=settings["effort"], thinking=settings["thinking"])


def run(inputs: dict, settings: dict) -> dict:
    kind, req = request(inputs, settings)
    record = client().call(req)
    if record["status"] == "error":
        raise RuntimeError(record["error"])
    record["cost_usd"] = claude_client.claude_cost(settings["model"]["id"], record["usage"])
    return judge.outputs(record["status"], record["parsed"], kind, record["model_served"]) | {"_details": record}
