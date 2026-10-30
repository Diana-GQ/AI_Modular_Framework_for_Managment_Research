"""The synthetic competition's executive summaries (design, B4): for one
fictional venture, with its invented name and concept, Claude invents a team,
a pitch, a description and a two-page executive summary whose strength and
writing match the venture's hidden quality and quality of writing."""

from pathlib import Path

from components.shared import generation
from pipeline import models

PROMPTS = Path(__file__).resolve().parent / "prompts.yaml"


def level(z: float, levels: list) -> str:
    return next(text for threshold, text in levels if z >= threshold)


def run(inputs: dict, settings: dict) -> dict:
    v = inputs["venture"]
    p = models.load_prompts(PROMPTS)
    user = p["user"].format(
        name=inputs["concept"]["name"], concept=inputs["concept"]["concept"], company_type=v["company_type"], product_types=", ".join(v["product_types"]), fields=", ".join(v["fields"]),
        milestones=", ".join(v["milestones"]) or "none yet",
        entity=f"formed ({v['entity_type']})" if v["entity_formed"] else "not formed yet",
        website="yes" if v["has_website"] else "none yet",
        quality=level(v["quality"], p["quality"]), writing=level(v["writing"], p["writing"]))
    parsed, record = generation.ask(p["system"], user, p["schema"], settings)
    return {**{k: parsed[k] for k in ("team", "pitch", "description", "summary")}, "_details": record}
