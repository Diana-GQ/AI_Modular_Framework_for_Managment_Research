"""The synthetic ventures' concepts (design, B4): Claude invents a name and a
one-sentence concept for every venture of the synthetic competition in one
call, so that the ventures differ from one another as a real competition's
entries do. Each concept fits the venture's answers on the application form."""

from pathlib import Path

from components.shared import generation
from pipeline import models

PROMPTS = Path(__file__).resolve().parent / "prompts.yaml"


def describe(v: dict) -> str:
    return (f"- Venture {v['venture']}: {v['company_type']}; products: {', '.join(v['product_types'])};"
            f" fields: {', '.join(v['fields'])}; milestones: {', '.join(v['milestones']) or 'none yet'}")


def run(inputs: dict, settings: dict) -> dict:
    p = models.load_prompts(PROMPTS)
    ventures = inputs["ventures"]
    user = p["user"].format(n=len(ventures), ventures="\n".join(describe(v) for v in ventures))
    parsed, record = generation.ask(p["system"], user, p["schema"], settings)
    concepts = {c["venture"]: c for c in parsed["concepts"]}
    if sorted(concepts) != sorted(v["venture"] for v in ventures):
        raise RuntimeError("the concepts do not match the ventures one to one")
    return {"concepts": [{"venture": v["venture"], "name": concepts[v["venture"]]["name"],
                          "concept": concepts[v["venture"]]["concept"]} for v in ventures], "_details": record}
