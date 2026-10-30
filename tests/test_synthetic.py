import itertools
import json
import re

import numpy as np
import pandas as pd

from components.shared import generation
from pipeline.runner import Component
from pipeline.stages import synthetic
from tests import fakes

CRITERIA = ("concept", "business_model", "market", "written_work", "investor_interest")


def test_design_is_reproducible_and_complete():
    c = Component("synthetic_competition")
    first = c.module.run({"seed": 7}, c.settings)
    assert first == c.module.run({"seed": 7}, c.settings)
    s = c.settings
    assert len(first["ventures"]) == s["entries"] and len(first["judges"]) == s["judges"]
    assert len(first["evaluations"]) == s["entries"] * s["judges_per_entry"]
    by_venture = pd.DataFrame(first["evaluations"]).groupby("venture")["judge"].nunique()
    assert (by_venture == s["judges_per_entry"]).all()
    for e in first["evaluations"]:
        assert all(isinstance(e[k], int) and 1 <= e[k] <= 10 for k in CRITERIA)
        assert abs(e["weighted"] - sum(s["weights"][k] * e[k] for k in CRITERIA)) < 1e-9
    assert len(first["advanced"]) == round(s["advance_share"] * s["entries"])


def test_simulated_judges_have_a_halo_and_the_settings_means():
    c = Component("synthetic_competition")
    settings = dict(c.settings, entries=600, judges=60)
    ev = pd.DataFrame(c.module.run({"seed": 3}, settings)["evaluations"])
    for k in CRITERIA:
        assert abs(ev[k].mean() - settings["criteria"][k]["mean"]) < 0.4
    corr = ev[list(CRITERIA)].corr().to_numpy()
    assert corr[np.triu_indices(5, 1)].mean() > 0.5


def test_pdf_writer_gives_files_the_extractor_reads(tmp_path):
    text = "\n".join(f"Paragraph {i}: the team (three founders) sells — by subscription — to commuters." for i in range(80))
    path = tmp_path / "summary.pdf"
    path.write_bytes(synthetic.pdf_bytes("Rainy Day Rentals", text))
    out = Component("text_extractor").run({"file": {"path": str(path), "sha256": synthetic.sha256_file(path)}}).outputs
    assert out["pages"] > 1 and not out["needs_ocr"]
    assert "Rainy Day Rentals" in out["text"] and "Paragraph 79" in out["text"]


def fake_generation(monkeypatch):
    counter = itertools.count(1)

    def reply(request):
        properties = request["output_config"]["format"]["schema"]["properties"]
        if "concepts" in properties:
            numbers = [int(n) for n in re.findall(r"^- Venture (\d+):", request["messages"][0]["content"], re.M)]
            body = {"concepts": [{"venture": n, "name": f"Venture Number {n}", "concept": f"Umbrellas for city {n}."} for n in numbers]}
        elif "summary" in properties:
            n = next(counter)
            body = {"team": [f"Founder {n}A", f"Founder {n}B"], "pitch": "Umbrellas by subscription.",
                    "description": "We rent umbrellas to commuters.", "summary": f"Problem\nCommuters in city {n} get wet.\n" * 40}
        else:
            body = {k: "A clear need, weakly evidenced." for k in ("concept", "business_model", "market", "written_work", "investor_interest")}
            body["concept_score_comment"] = ""
        return fakes.FakeResponse(request["model"], json.dumps(body))

    fake = fakes.claude_client(reply)
    monkeypatch.setattr(generation, "_client", fake)
    return fake


def test_build_writes_a_competition_the_pipeline_reads(monkeypatch, isolated_data):
    from pipeline.stages import pseudonymize, tables

    fake = fake_generation(monkeypatch)
    monkeypatch.setattr(synthetic, "SYNTHETIC", isolated_data)
    monkeypatch.setattr(synthetic, "REAL_TERMS", isolated_data / "absent.tsv")
    synthetic.build()
    design = Component("synthetic_competition").settings
    calls = 1 + design["entries"] * (1 + design["judges_per_entry"])
    assert len(fake.client.messages.requests) == calls
    built = json.loads((isolated_data / "synthetic.json").read_text())
    assert built["files"] == {"pdf": 35, "docx": 5} and built["real_terms_check"].startswith("not run")

    pseudonymize.main(synthetic.YEAR)
    result = tables.build(synthetic.YEAR)
    entries = pd.DataFrame(result.outputs["entries"])
    evaluations = pd.DataFrame(result.outputs["evaluations"])
    assert len(entries) == design["entries"] + 4 and entries["judged"].sum() == design["entries"]
    assert entries["has_summary"].sum() == design["entries"]
    assert entries["advanced_r2"].sum() == round(design["advance_share"] * design["entries"])
    scores = evaluations[evaluations["question"].isin(["Q2", "Q4", "Q6", "Q7", "Q9"])]
    assert len(scores) == 5 * design["entries"] * design["judges_per_entry"]
    # The empty comments on the concept score are left out, as the judging sheet leaves them blank.
    assert not (evaluations["question"] == "Q2c").any()
    terms = (isolated_data / "private" / "sensitive_terms.tsv").read_text()
    assert "Venture Number 1\n" in terms and "Judge 01" in terms and "@" not in terms

    # Built again, nothing is generated again, and the files are the same.
    before = (isolated_data / "manifests" / "2000_documents.csv").read_text()
    synthetic.build()
    assert len(fake.client.messages.requests) == calls
    assert (isolated_data / "manifests" / "2000_documents.csv").read_text() == before


def test_texts_matching_the_real_term_list_are_written_again(monkeypatch, isolated_data):
    fake = fake_generation(monkeypatch)
    monkeypatch.setattr(synthetic, "SYNTHETIC", isolated_data)
    rounds = []

    def matches(texts):
        # The concepts never match; the first summary matches on the first attempt only.
        if len(texts) == Component("synthetic_competition").settings["entries"]:
            return [False] * len(texts)
        rounds.append(len(rounds) + 1)
        return [len(rounds) == 1 and i == 0 for i in range(len(texts))]

    monkeypatch.setattr(synthetic, "real_term_matches", matches)
    synthetic.build()
    design = Component("synthetic_competition").settings
    # One summary written again, and its three judges' comments with it.
    assert len(fake.client.messages.requests) == 1 + design["entries"] * (1 + design["judges_per_entry"]) + 1 + design["judges_per_entry"]
    built = json.loads((isolated_data / "synthetic.json").read_text())
    assert built["written_again"]["summaries"] == 1 and built["written_again"]["sets_of_comments"] == 0
    assert built["real_terms_check"].startswith("passed") and rounds == [1, 2]
