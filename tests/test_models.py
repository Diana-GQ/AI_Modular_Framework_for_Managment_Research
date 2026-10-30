import pytest

from pipeline import claude_client, models, qwen_client
from tests import fakes

REQUEST = claude_client.ClaudeClient.build_request(
    model="claude-sonnet-5-5", system="System.", document_part="Business plan text:\n\nX\n\n",
    question_part="Question: Q?", schema={"type": "object"}, max_tokens=64, effort="high",
    thinking={"type": "between_tools"})


def test_request_shape():
    assert REQUEST["thinking"] == {"type": "between_tools"}
    assert REQUEST["output_config"] == {"effort": "high", "format": {"type": "json_schema", "schema": {"type": "object"}}}
    document, question = REQUEST["messages"][0]["content"]
    assert document["cache_control"] == {"type": "ephemeral"} and "cache_control" not in question
    # No sampling settings (the model rejects them) and no fallbacks to other models.
    for key in ("temperature", "top_p", "top_k", "seed", "fallbacks", "metadata"):
        assert key not in REQUEST


@pytest.mark.parametrize("text,stop,status,parsed", [
    ('{"score": 7}', "end_turn", "ok", {"score": 7}),
    ("not json", "end_turn", "unparseable", None),
    ('{"response": "cut', "max_tokens", "max_tokens", None),
    (None, "refusal", "refusal", None),
    ('{"score": 7}', "pause_turn", "other", None),
])
def test_call_statuses(text, stop, status, parsed):
    client = fakes.claude_client(lambda r: fakes.FakeResponse(r["model"], text, stop))
    record = client.call(REQUEST)
    assert record["status"] == status and record["parsed"] == parsed
    assert record["request"] == REQUEST and record["request_id"] == "req_test"
    assert record["usage"]["input_tokens"] == 1500


def test_answer_from_another_model_is_an_error():
    client = fakes.claude_client(lambda r: fakes.FakeResponse("claude-sonnet-5", '{"score": 7}'))
    with pytest.raises(models.ModelMismatch):
        client.call(REQUEST)


def test_cost():
    usage = {"input_tokens": 1_000_000, "output_tokens": 100_000, "cache_read_input_tokens": 1_000_000,
             "cache_creation_input_tokens": 0}
    assert claude_client.claude_cost("claude-sonnet-5-5", usage) == pytest.approx(2.0 + 1.0 + 0.2)


@pytest.mark.parametrize("result,kind,status,parsed", [
    ({"text": '{"score": 3}', "finish_reason": "stop", "model": "m"}, "score", "ok", {"score": 3}),
    ({"text": " A plain answer.\n", "finish_reason": "stop", "model": "m"}, "written", "ok", {"response": "A plain answer."}),
    ({"text": "A long answer that was cut", "finish_reason": "length", "model": "m"}, "written", "max_tokens", None),
    ({"text": "{", "finish_reason": "stop", "model": "m"}, "score", "unparseable", None),
    ({"text": "  ", "finish_reason": "stop", "model": "m"}, "written", "unparseable", {"response": ""}),
])
def test_parse_qwen(result, kind, status, parsed):
    record = qwen_client.parse_qwen(result, kind)
    assert record["status"] == status and record["parsed"] == parsed
