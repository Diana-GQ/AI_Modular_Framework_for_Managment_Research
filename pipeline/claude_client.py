"""The Claude judge's client: Anthropic's API.

Every call returns a record with the full request, the full response, the
parsed answer, a status and the usage; the component stores it in its
provenance record. Fallbacks to other models are never requested, and a
response from any model other than the one requested is an error.
"""

import json
import time

from dotenv import load_dotenv

from .models import ModelMismatch
from .paths import ROOT

# Anthropic list prices on 2026-10-12, US dollars per million tokens.
PRICES = {
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20, "cache_write_5m": 2.50},
}


def claude_cost(model: str, usage: dict) -> float:
    p = PRICES[model]
    return (usage.get("input_tokens", 0) * p["input"]
            + usage.get("output_tokens", 0) * p["output"]
            + usage.get("cache_read_input_tokens", 0) * p["cache_read"]
            + usage.get("cache_creation_input_tokens", 0) * p["cache_write_5m"]) / 1e6


class ClaudeClient:
    def __init__(self, max_retries: int = 6, timeout: float = 120.0):
        import anthropic

        load_dotenv(ROOT / ".env")
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=max_retries, timeout=timeout)

    @staticmethod
    def build_request(*, model: str, system: str, document_part: str, question_part: str, schema: dict,
                      max_tokens: int, effort: str, thinking: dict) -> dict:
        return {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "thinking": thinking,
            "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": document_part, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": question_part},
            ]}],
        }

    def call(self, request: dict) -> dict:
        started = time.time()
        try:
            response = self.client.messages.create(**request)
        except self.anthropic.APIStatusError as e:
            return {"status": "error", "error": f"HTTP {e.status_code}: {e.message}", "request": request,
                    "response": None, "parsed": None, "usage": {}, "seconds": time.time() - started}
        except self.anthropic.APIConnectionError as e:
            return {"status": "error", "error": f"connection: {e}", "request": request, "response": None,
                    "parsed": None, "usage": {}, "seconds": time.time() - started}
        raw = response.to_dict()
        if response.model != request["model"]:
            raise ModelMismatch(f"requested {request['model']}, answered by {response.model}")
        usage = response.usage.to_dict() if response.usage else {}
        record = {"request": request, "response": raw, "usage": usage, "request_id": response._request_id,
                  "model_served": response.model, "stop_reason": response.stop_reason,
                  "seconds": time.time() - started, "parsed": None}
        if response.stop_reason == "refusal":
            record["status"] = "refusal"
            return record
        if response.stop_reason != "end_turn":
            record["status"] = "max_tokens" if response.stop_reason == "max_tokens" else "other"
            return record
        text = next((b.text for b in response.content if b.type == "text"), None)
        try:
            record["parsed"] = json.loads(text) if text is not None else None
            record["status"] = "ok" if record["parsed"] is not None else "unparseable"
        except json.JSONDecodeError:
            record["status"] = "unparseable"
        return record

