"""Arranges a year's round 1 records into the four analysis tables of the
design's Section 1.3: entries, documents, evaluations and judges, linked by
codes. Names, email addresses and websites are dropped, and identities are
replaced by their codes from the private key."""

import unicodedata

from openpyxl import load_workbook

from pipeline import pseudonyms

QUESTIONS = ("Q1", "Q2", "Q2c", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "weighted")
SCORES = {"Q2", "Q4", "Q6", "Q7", "Q9", "weighted"}
YES_NO = {"Yes": True, "No": False}
ENTRY_COLUMNS = ("year", "entry", "submitted", "judged", "has_summary", "r1_rank", "advanced_r2", "finalist", "winner",
                 "pitch", "description", "product_type", "company_type", "fields", "milestones", "milestones_other",
                 "entity_formed", "entity_type", "has_website")


def _clean(header) -> str:
    text = unicodedata.normalize("NFKC", str(header or "")).replace("", " ")
    return " ".join(text.split())


def read_sheet(workbook, spec: dict) -> list[dict]:
    """The rows of one sheet as dictionaries with the names given in the
    settings. Each column's header must contain the expected fragments, so a
    changed layout stops the run instead of filling the wrong column."""
    rows = list(workbook[spec["sheet"]].iter_rows(values_only=True))
    header = [_clean(h) for h in rows[0]]
    for name, col in spec["columns"].items():
        i = col["column"]
        if i >= len(header) or not all(f in header[i] for f in col["header"]):
            raise ValueError(f"sheet {spec['sheet']!r}, column {i} ({name}): header does not match the settings")
    out = []
    for row in rows[1:]:
        if not any(v not in (None, "") for v in row):
            continue
        record = {}
        for name, col in spec["columns"].items():
            value = row[col["column"]] if col["column"] < len(row) else None
            if isinstance(value, str):
                value = value.strip() or None
            record[name] = value
        out.append(record)
    return out


def read(workbook_path: str, settings: dict) -> tuple[list[dict], list[dict]]:
    workbook = load_workbook(workbook_path)
    return read_sheet(workbook, settings["applications"]), read_sheet(workbook, settings["judging"])


def run(inputs: dict, settings: dict) -> dict:
    year = inputs["year"]
    key = pseudonyms.load(inputs["key"]["path"])
    applications, judging = read(inputs["workbook"]["path"], settings)

    def entry_code(identifier):
        return pseudonyms.code(key, "entry", identifier)

    documents = []
    for x in inputs["extractions"]:
        documents.append({
            "year": year, "entry": entry_code(x["entry_identifier"]), "file_type": x["file_type"],
            "sha256": x["sha256"], "text": x["text"], "pages": x["pages"], "words": x["words"],
            "method": x["method"], "needs_ocr": x["needs_ocr"], "extraction": x["extraction"],
        })
    with_summary = {d["entry"] for d in documents}

    evaluations, judges, rank = [], set(), {}
    for row in judging:
        entry, judge = entry_code(row["entry_identifier"]), pseudonyms.code(key, "judge", row["judge_email"])
        judges.add(judge)
        rank[entry] = int(row["rank"])
        for q in QUESTIONS:
            value = row[q]
            if value is None:
                continue
            evaluations.append({
                "year": year, "entry": entry, "evaluator": judge, "evaluator_type": "human", "question": q, "run": 1,
                "score": float(value) if q in SCORES else None, "text": None if q in SCORES else str(value),
            })

    entries = {}
    for row in applications:
        code = entry_code(row["entry_identifier"])
        entries[code] = {
            "year": year, "entry": code, "submitted": row["submitted"] is not None,
            "judged": code in rank, "has_summary": code in with_summary, "r1_rank": rank.get(code),
            "advanced_r2": YES_NO.get(row["advanced_r2"]), "finalist": None, "winner": None,
            "pitch": row["pitch"], "description": row["description"], "product_type": row["product_type"],
            "company_type": row["company_type"], "fields": row["fields"], "milestones": row["milestones"],
            "milestones_other": row["milestones_other"], "entity_formed": YES_NO.get(row["entity_formed"]),
            "entity_type": row["entity_type"], "has_website": row["website"] is not None,
        }
    for code in rank.keys() - entries.keys():
        # Judged, but missing from the applications sheet: what is known is that it was judged.
        entries[code] = dict.fromkeys(ENTRY_COLUMNS) | {
            "year": year, "entry": code, "judged": True, "has_summary": code in with_summary, "r1_rank": rank[code]}

    order = {q: i for i, q in enumerate(QUESTIONS)}
    return {
        "entries": sorted(entries.values(), key=lambda r: r["entry"]),
        "documents": sorted(documents, key=lambda r: (r["entry"], r["sha256"])),
        "evaluations": sorted(evaluations, key=lambda r: (r["entry"], r["evaluator"], order[r["question"]])),
        "judges": [{"judge": j} for j in sorted(judges)],
    }
