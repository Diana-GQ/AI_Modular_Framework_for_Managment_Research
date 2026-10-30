"""What the two AI judges share: the prompts, and turning an answer into the
judges' common outputs (design, Section 2.1)."""

from pathlib import Path

from pipeline import models

PROMPTS = Path(__file__).resolve().parent / "judge_prompts.yaml"


def prompts() -> dict:
    return models.load_prompts(PROMPTS)


def message_parts(p: dict, inputs: dict) -> tuple[str, dict]:
    """The question's kind, and the parts of the user message for this summary and question."""
    question = p["questions"][inputs["question"]]
    document_part, question_part = models.user_blocks(p["document_part"], inputs["summary"],
                                                      p["question_part"], question["text"])
    return question["kind"], {"system": p["system"], "document_part": document_part,
                              "question_part": question_part, "schema": p["schemas"][question["kind"]]}


def outputs(status: str, parsed: dict | None, kind: str, model_served: str | None) -> dict:
    ok = status == "ok"
    return {"status": status, "model_served": model_served,
            "answer": parsed["response"] if ok and kind == "written" else None,
            "score": parsed["score"] if ok and kind == "score" else None}
