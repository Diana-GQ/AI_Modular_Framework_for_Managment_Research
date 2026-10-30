import json

import pytest

from pipeline import pseudonyms
from pipeline.runner import Component
from tests import synthetic

SCORES = {"Q2": 7, "Q4": 6, "Q6": 8, "Q7": 5, "Q9": 6}
TEXTS = {"Q1": "Clear need.", "Q3": "Plausible model.", "Q5": "Large market.", "Q8": "Shorten it.", "Q10": "Strong team."}


def application(identifier, submitted=True, advanced="No"):
    return {"entry_identifier": identifier, "submitted": "2019-01-01 10:00" if submitted else None,
            "advanced_r2": advanced, "pitch": "Umbrellas by subscription", "description": "We rent umbrellas.",
            "product_type": "Physical product", "company_type": "Non-Internet", "fields": "Retail",
            "milestones": "Prototype", "milestones_other": None, "entity_formed": "Yes", "entity_type": "LLC",
            "website": "https://example.org" if submitted else None}


def evaluation(identifier, judge, rank, comment="Good idea."):
    row = {"rank": rank, "entry_identifier": identifier, "judge_email": judge, "Q2c": comment, **SCORES, **TEXTS}
    row["weighted"] = 0.2 * 7 + 0.2 * 6 + 0.2 * 8 + 0.1 * 5 + 0.3 * 6
    return row


@pytest.fixture
def records(tmp_path):
    tables = Component("records_tables")
    judges = ["judge-one", "Judge-Two", "judge-three"]
    applications = [application("app-a", advanced="Yes"), application("app-b"), application("app-c", submitted=False)]
    judging = [evaluation("app-a", j, 1) for j in judges]
    judging += [evaluation("app-d", j, 2, comment=None if i == 0 else "Fine.") for i, j in enumerate(judges)]
    book = synthetic.workbook(tmp_path / "export.xlsx", tables.settings, applications, judging)
    key = tmp_path / "private" / "code_key.csv"
    pseudonyms.assign("entry", ["app-a", "app-b", "app-c", "app-d"], 2019, key)
    pseudonyms.assign("judge", judges, 2019, key)
    extractions = [{"entry_identifier": i, "file_type": "pdf", "sha256": f"{n}" * 64, "text": "Summary text.",
                    "pages": 2, "words": 2, "method": "pypdfium2", "needs_ocr": False, "extraction": "0" * 64}
                   for n, i in ((1, "app-a"), (2, "app-c"))]
    result = tables.run({"year": 2019, "workbook": synthetic.file_ref(book), "key": synthetic.file_ref(key),
                         "extractions": extractions})
    return result.outputs, pseudonyms.load(key)


def test_entries(records):
    out, key = records
    entries = {e["entry"]: e for e in out["entries"]}
    code = lambda i: key[("entry", i)]
    assert len(entries) == 4
    a, b, c, d = (entries[code(i)] for i in ("app-a", "app-b", "app-c", "app-d"))
    assert (a["submitted"], a["judged"], a["has_summary"], a["advanced_r2"], a["r1_rank"]) == (True, True, True, True, 1)
    assert (b["judged"], b["has_summary"], b["advanced_r2"]) == (False, False, False)
    assert (c["submitted"], c["has_summary"], c["has_website"]) == (False, True, False)
    # Judged but missing from the applications sheet: only what the judging sheet shows.
    assert (d["submitted"], d["judged"], d["r1_rank"], d["pitch"]) == (None, True, 2, None)
    assert a["finalist"] is None and a["winner"] is None


def test_evaluations(records):
    out, key = records
    rows = out["evaluations"]
    # Two entries, three judges, twelve items each, less one empty optional comment.
    assert len(rows) == 2 * 3 * 12 - 1
    assert {r["evaluator_type"] for r in rows} == {"human"} and {r["run"] for r in rows} == {1}
    score = [r for r in rows if r["question"] == "Q9"][0]
    assert score["score"] == 6.0 and score["text"] is None
    text = [r for r in rows if r["question"] == "Q10"][0]
    assert text["text"] == "Strong team." and text["score"] is None
    weighted = [r for r in rows if r["question"] == "weighted"][0]
    assert weighted["score"] == pytest.approx(6.5)
    assert len(out["judges"]) == 3


def test_no_identities_in_the_tables(records):
    out, _ = records
    dump = json.dumps(out).lower()
    assert "judge-" not in dump
    assert not any(f"app-{x}" in dump for x in "abcd")


def test_changed_layout_is_refused(tmp_path):
    tables = Component("records_tables")
    settings = json.loads(json.dumps(tables.settings))
    settings["judging"]["columns"]["Q9"]["header"] = ["Weighted average"]
    book = synthetic.workbook(tmp_path / "export.xlsx", settings, [application("app-a")], [evaluation("app-a", "judge-x", 1)])
    with pytest.raises(ValueError, match="header does not match"):
        tables.module.read(str(book), tables.settings)
