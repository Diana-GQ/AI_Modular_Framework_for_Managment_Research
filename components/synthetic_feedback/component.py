"""The synthetic judges' comments (design, B4): for one evaluation, Claude
writes, as the fictional judge, the comments on the six written questions of
the judging form, consistent with the scores the simulation gave."""

from pathlib import Path

from components.shared import generation
from pipeline import models

PROMPTS = Path(__file__).resolve().parent / "prompts.yaml"


def run(inputs: dict, settings: dict) -> dict:
    p = models.load_prompts(PROMPTS)
    user = p["user"].format(persona=inputs["persona"], summary=inputs["summary"], **inputs["scores"])
    parsed, record = generation.ask(p["system"], user, p["schema"], settings)
    return {"comments": parsed, "_details": record}
