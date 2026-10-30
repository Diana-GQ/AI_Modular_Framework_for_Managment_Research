"""What the synthetic competition's writers share: one call to Claude with a
structured answer. A failed, refused or cut-off call raises, so nothing is
stored and a later run tries again."""

import threading

from pipeline import claude_client

_client = None
_lock = threading.Lock()


def client() -> claude_client.ClaudeClient:
    global _client
    with _lock:
        if _client is None:
            _client = claude_client.ClaudeClient()
    return _client


def ask(system: str, user: str, schema: dict, settings: dict) -> tuple[dict, dict]:
    request = {"model": settings["model"]["id"], "max_tokens": settings["max_tokens"], "system": system,
               "thinking": settings["thinking"],
               "output_config": {"effort": settings["effort"], "format": {"type": "json_schema", "schema": schema}},
               "messages": [{"role": "user", "content": user}]}
    record = client().call(request)
    if record["status"] != "ok":
        raise RuntimeError(f"generation failed: {record['status']} {record.get('error', '')}")
    record["cost_usd"] = claude_client.claude_cost(settings["model"]["id"], record["usage"])
    return record["parsed"], record
