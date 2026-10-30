"""Stand-ins for Anthropic's API and the Modal deployment, so tests make no network calls."""

import json
from types import SimpleNamespace


class FakeUsage(SimpleNamespace):
    def to_dict(self):
        return dict(self.__dict__)


class FakeResponse:
    def __init__(self, model, text, stop_reason="end_turn"):
        self.model, self.stop_reason, self._request_id = model, stop_reason, "req_test"
        self.content = [SimpleNamespace(type="text", text=text)] if text is not None else []
        self.usage = FakeUsage(input_tokens=1500, output_tokens=40, cache_read_input_tokens=0,
                               cache_creation_input_tokens=0)

    def to_dict(self):
        return {"model": self.model, "stop_reason": self.stop_reason,
                "content": [{"type": b.type, "text": b.text} for b in self.content]}


class FakeMessages:
    def __init__(self, reply):
        self.reply, self.requests = reply, []

    def create(self, **request):
        self.requests.append(request)
        return self.reply(request)


def claude_client(reply):
    """A ClaudeClient whose API answers with reply(request) -> FakeResponse."""
    import anthropic

    from pipeline.claude_client import ClaudeClient

    client = ClaudeClient.__new__(ClaudeClient)
    client.anthropic = anthropic
    client.client = SimpleNamespace(messages=FakeMessages(reply))
    return client


def answer_for(request) -> str:
    """A well-formed answer to whatever the request asks for: Claude's JSON
    schemas, or the open-weight judge's score pattern or plain text."""
    if "output_config" in request:
        score = "score" in request["output_config"]["format"]["schema"]["properties"]
        return json.dumps({"score": 7} if score else {"response": "A clear need, weakly evidenced."})
    return '{"score": 7}' if request["structured_outputs"] else "A clear need, weakly evidenced."


class FakeQwenJudge:
    """Answers like QwenJudge.generate, recording each batch it receives."""

    def __init__(self, model, revision):
        self.model, self.revision, self.batches = model, revision, []
        self.generate = SimpleNamespace(remote=self._generate)

    def _generate(self, requests):
        self.batches.append(requests)
        return [{"text": answer_for(r), "token_ids": [1, 2, 3], "finish_reason": "stop", "prompt_tokens": 1500,
                 "output_tokens": 3, "model": self.model, "revision": self.revision} for r in requests]
