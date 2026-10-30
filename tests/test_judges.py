import pytest

from components.shared import judge
from pipeline import models
from pipeline.runner import Component, RunError
from tests import fakes

SUMMARY = "We rent umbrellas by subscription to commuters in rainy cities."
AUTHORS_SYSTEM = ("You are an expert evaluator in entrepreneurship and early-stage venture assessment. "
                  "You are analytical, objective, and concise but insightful. No fluff. You do not act as an "
                  "assistant. You act as a structured evaluation engine.")


def inputs(question="Q1", run=1):
    return {"entry": "E-000000", "summary": SUMMARY, "question": question, "run": run}


def test_prompts_follow_the_design():
    p = judge.prompts()
    assert p["system"] == AUTHORS_SYSTEM
    assert sorted(p["questions"], key=lambda q: int(q[1:])) == [f"Q{i}" for i in range(1, 11)]
    assert {q: p["questions"][q]["kind"] for q in ("Q2", "Q4", "Q6", "Q7", "Q9")} == dict.fromkeys(("Q2", "Q4", "Q6", "Q7", "Q9"), "score")
    kind, parts = judge.message_parts(p, inputs("Q8"))
    assert kind == "written"
    assert parts["document_part"] + parts["question_part"] == (
        f"Business plan text:\n\n{SUMMARY}\n\nQuestion: What can the team do to improve their written submission?")


def test_claude_request():
    c = Component("claude_judge")
    kind, req = c.module.request(inputs("Q9"), c.settings)
    assert kind == "score" and req["model"] == "claude-sonnet-5-5" and req["max_tokens"] == 64
    assert req["system"] == AUTHORS_SYSTEM
    assert req["output_config"]["format"]["schema"]["properties"]["score"]["enum"] == list(range(1, 11))
    # The entry code and the run number are not sent.
    assert "E-000000" not in str(req) and "run" not in str(req["messages"])


def test_claude_runs_and_stores(monkeypatch):
    c = Component("claude_judge")
    fake = fakes.claude_client(lambda r: fakes.FakeResponse(r["model"], fakes.answer_for(r)))
    monkeypatch.setattr(c.module, "_client", fake)
    results = c.run_batch([inputs("Q1", 1), inputs("Q2", 1), inputs("Q2", 2)], workers=3)
    assert [r.outputs["status"] for r in results] == ["ok"] * 3
    assert results[0].outputs["answer"] and results[0].outputs["score"] is None
    assert results[1].outputs["score"] == 7 and results[1].outputs["answer"] is None
    assert len(fake.client.messages.requests) == 3
    record = c.store.get_record("claude_judge", results[1].record_id)
    assert record["details"]["request"]["model"] == "claude-sonnet-5-5" and record["details"]["cost_usd"] > 0
    # Stored answers are reused, not regenerated.
    assert c.run(inputs("Q2", 2)).cached and len(fake.client.messages.requests) == 3


def test_claude_failures_are_not_stored(monkeypatch):
    import anthropic
    import httpx2

    def fail(request):
        raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))

    c = Component("claude_judge")
    monkeypatch.setattr(c.module, "_client", fakes.claude_client(fail))
    [result] = c.run_batch([inputs()])
    assert isinstance(result, RunError) and c.cached(inputs()) is None


def test_claude_refusal_is_stored_as_missing(monkeypatch):
    c = Component("claude_judge")
    monkeypatch.setattr(c.module, "_client", fakes.claude_client(lambda r: fakes.FakeResponse(r["model"], None, "refusal")))
    out = c.run(inputs("Q4")).outputs
    assert out == {"status": "refusal", "answer": None, "score": None, "model_served": "claude-sonnet-5-5"}


def qwen_with_fake(monkeypatch, revision=None):
    c = Component("qwen_judge")
    fake = fakes.FakeQwenJudge(c.settings["model"]["id"], revision or c.settings["model"]["revision"])
    monkeypatch.setattr(c.module, "_session", {"judge": fake, "environment": {"gpu": "test"}, "started": 0})
    return c, fake


def test_qwen_seeds_follow_runs(monkeypatch):
    c, fake = qwen_with_fake(monkeypatch)
    results = c.run_batch([inputs("Q6", run) for run in (1, 2, 5)])
    assert [r.outputs["score"] for r in results] == [7, 7, 7]
    [batch] = fake.batches
    assert [r["sampling"]["seed"] for r in batch] == [1, 2, 5]
    assert batch[0]["sampling"]["temperature"] == 0.7 and batch[0]["sampling"]["watermarking"] is False
    assert batch[0]["structured_outputs"] == {"regex": '\\{"score": (10|[1-9])\\}'}
    assert batch[0]["messages"][0] == {"role": "system", "content": AUTHORS_SYSTEM}


def test_qwen_written_answers_are_plain_text(monkeypatch):
    c, fake = qwen_with_fake(monkeypatch)
    out = c.run(inputs("Q3")).outputs
    assert out["status"] == "ok" and out["answer"] == "A clear need, weakly evidenced." and out["score"] is None
    assert fake.batches[0][0]["structured_outputs"] is None
    assert fake.batches[0][0]["sampling"]["max_tokens"] == 8192


def test_qwen_answer_from_another_revision_is_an_error(monkeypatch):
    c, _ = qwen_with_fake(monkeypatch, revision="0" * 40)
    with pytest.raises(models.ModelMismatch):
        c.run_batch([inputs("Q1")])


def test_qwen_contract_matches_the_deployment():
    c = Component("qwen_judge")
    c.module.check_pins(c.settings)
    with pytest.raises(models.ModelMismatch):
        c.module.check_pins(dict(c.settings, model=dict(c.settings["model"], gpu="A100")))
