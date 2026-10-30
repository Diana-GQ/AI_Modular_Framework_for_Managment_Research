"""Plan task 6.4, B4: the synthetic competition that the public repository carries.

    uv run python -m pipeline.stages.synthetic build            # generate the records and files
    uv run python -m pipeline.stages.synthetic run              # run the whole pipeline on them

The synthetic competition is a fictional edition (year 2000) with the same
files and layout as the real ones, kept in synthetic/data/ (COMPAI_DATA): an
export workbook with an applications sheet and a judging sheet, executive
summaries as PDF and Word files, the document inventory, and a list of the
fictional names for the name filters. Its ventures, judges and scores come
from the synthetic_competition component; its summaries and comments from
synthetic_summary and synthetic_feedback. No record of the real competition
enters it: the build checks every generated text against the real records'
sensitive-term list, where that list exists, and writes a text that matches
again, under a new attempt number; it stops if a text still matches after
MAX_ATTEMPTS attempts.
The public repository carries its stored outputs and tables (publish_outputs).
"""

import csv
import io
import json
import os
import re
import shutil
import sys
import textwrap
import zipfile
from pathlib import Path

from ..hashing import sha256_file

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC = ROOT / "synthetic" / "data"
YEAR = 2000
REAL_TERMS = ROOT / "data" / "private" / "sensitive_terms.tsv"
# Who ran each step, in the published provenance records.
PUBLISHED_AGENT = "the authors"

APPLICATION_HEADERS = [
    "Entry", "Identifier", "Time of entry", "Submitted?", "Name", "Email", "Role",
    "Advanced to Round 1", "Advanced to Round 2", "Advanced to Round 3", "How did you hear about the competition?",
    "Give us your high-level pitch", "Describe your business", "Which type of product are you building?",
    "Which best fits your company?", "Which fields/tags are your startup involved in?",
    "Which milestones have you reached to date?", "If other(s), please specify:",
    "Do you currently have an entity formed for your company?", "If you have an entity formed, what type of entity?",
    "Do you have a website for your business? Please share the address.",
    *[f"Eligibility statement {i}" for i in range(1, 13)], "Terms accepted",
    "Executive summary upload", "Terms of round 2 accepted", "Proof of student status"]
JUDGING_HEADERS = [
    "Rank", "Entry", "Entry identifier", "Judge Email", "Judge Name",
    "Discuss the overall quality of the business concept or idea. Address whether the offering addresses a real and clearly identified pain or need in a unique and compelling way.",
    "Please rate the quality of the company concept / idea on a scale of 1-10 - Score",
    "Please rate the quality of the company concept / idea on a scale of 1-10 - Applicant Feedback",
    "Comment on the viability and scalability of the business model and strategy. - Applicant Feedback",
    "Please rate the viability and scalability of the business model and strategy on a scale from 1-10. - Score",
    "Please share your thoughts on the market attractiveness and exit potential. - Applicant Feedback",
    "Please rate the market attractiveness and exit potential on a scale from 1-10. - Score",
    "Please rate the quality of the written work for this executive summary on a scale from 1-10. - Score",
    "What can the team do to improve their written submission? - Applicant Feedback",
    "You are an early stage investor considering this as an investment opportunity. Please rate your interest level on a scale from 1-10. - Score",
    "Please share the strengths and weaknesses that you considered to arrive at your answer. - Applicant Feedback",
    "Weighted average"]


def use_synthetic_data() -> None:
    os.environ["COMPAI_DATA"] = str(SYNTHETIC)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def identifier(rng) -> str:
    return "".join(rng.choice(list("0123456789abcdef"), size=20))


# ---- Files ---------------------------------------------------------------

def pdf_bytes(title: str, text: str, lines_per_page: int = 60, width: int = 95) -> bytes:
    """A plain PDF with Helvetica text, wrapped and paginated."""
    lines = [title, ""]
    for paragraph in text.splitlines():
        lines += textwrap.wrap(paragraph, width) if paragraph.strip() else [""]
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]

    def esc(s: str) -> bytes:
        s = (s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
             .replace("–", "-").replace("—", "-").replace("•", "-"))
        b = s.encode("cp1252", "replace")
        return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", None,
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for page in pages:
        body = b"BT /F1 10 Tf 12 TL 56 760 Td " + b" T* ".join(b"(" + esc(line) + b") Tj" for line in page) + b" ET"
        objects.append(b"<< /Length " + str(len(body)).encode() + b" >>\nstream\n" + body + b"\nendstream")
        content = len(objects)
        objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents "
                       + str(content).encode() + b" 0 R >>")
        kids.append(len(objects))
    objects[1] = b"<< /Type /Pages /Kids [" + b" ".join(f"{k} 0 R".encode() for k in kids) + b"] /Count " + str(len(kids)).encode() + b" >>"
    out, offsets = io.BytesIO(), []
    out.write(b"%PDF-1.4\n")
    for i, obj in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for o in offsets:
        out.write(f"{o:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def fixed_zip(data: bytes) -> bytes:
    """A Word or Excel file with its dates fixed, so that building again gives the same bytes."""
    src, out = zipfile.ZipFile(io.BytesIO(data)), io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in src.infolist():
            body = src.read(item.filename)
            if item.filename == "docProps/core.xml":
                body = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*", rb"\g<1>2000-01-01T00:00:00Z", body)
            info = zipfile.ZipInfo(item.filename, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, body)
    return out.getvalue()


def docx_bytes(title: str, text: str) -> bytes:
    from docx import Document

    doc = Document()
    doc.add_paragraph(title)
    for paragraph in text.splitlines():
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    buffer = io.BytesIO()
    doc.save(buffer)
    return fixed_zip(buffer.getvalue())


# ---- Build ---------------------------------------------------------------

MAX_ATTEMPTS = 5


def generated(component, results) -> list:
    """The outputs of a generator's batch; stops on any failure."""
    from ..runner import RunError

    failed = [r for r in results if isinstance(r, RunError)]
    if failed:
        sys.exit(f"{len(failed)} {component.contract.component} calls failed ({failed[0].error[:120]});"
                 " run build again to retry them")
    return [r.outputs for r in results]


def cost(component) -> float:
    """What all the generator's stored calls under its configuration cost, every attempt included."""
    name, total = component.contract.component, 0.0
    for path in (component.store.root / "index" / name / component.config_hash).glob("*.json"):
        entry = json.loads(path.read_text())
        for record in [entry["record"], *(r["record"] for r in entry["reruns"])]:
            total += component.store.get_record(name, record)["details"]["cost_usd"]
    return total


def real_term_matches(texts: list[str]) -> list[bool] | None:
    """No real name may enter: which generated texts match the real records'
    sensitive-term list. None where the list is absent (it is only on the authors' machines)."""
    if not REAL_TERMS.exists():
        return None
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_sensitive

    patterns, allow = check_sensitive.load_patterns()
    return [check_sensitive.scan("synthetic", t, patterns, allow, False) > 0 for t in texts]


def build() -> None:
    from datetime import date

    import numpy as np
    from openpyxl import Workbook

    from ..runner import Component

    use_synthetic_data()
    competition = Component("synthetic_competition")
    design_run = competition.run({"seed": YEAR})
    design = design_run.outputs
    ventures, judges = design["ventures"], design["judges"]
    print(f"design: {len(ventures)} ventures, {len(judges)} judges, {len(design['evaluations'])} evaluations", flush=True)

    # Texts that match the real records' term list are written again, under a new attempt number.
    # The ventures' names and concepts come first, invented together so that the ventures differ.
    concepter = Component("synthetic_concepts")
    rows = [{k: v[k] for k in ("venture", "company_type", "product_types", "fields", "milestones")} for v in ventures]
    for concept_attempt in range(1, MAX_ATTEMPTS + 1):
        concepts = concepter.run({"ventures": rows, "attempt": concept_attempt}).outputs["concepts"]
        matches = real_term_matches([f"{c['name']}\n{c['concept']}" for c in concepts])
        if not matches or not any(matches):
            break
        print(f"concepts, attempt {concept_attempt}: {sum(matches)} match the real records' term list;"
              " inventing them again", flush=True)
    else:
        sys.exit(f"the concepts still match the real records' term list after {MAX_ATTEMPTS} attempts")
    concept = {c["venture"]: {"name": c["name"], "concept": c["concept"]} for c in concepts}

    writer, commenter = Component("synthetic_summary"), Component("synthetic_feedback")
    persona = {j["judge"]: j["persona"] for j in judges}
    tries = {"summary": {}, "comments": {}}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        written = generated(writer, writer.run_batch(
            [{"venture": v, "concept": concept[v["venture"]], "attempt": tries["summary"].get(v["venture"], 1)}
             for v in ventures], workers=8))
        written = {v["venture"]: {**w, "name": concept[v["venture"]]["name"]} for v, w in zip(ventures, written)}
        keys = [(e["venture"], e["judge"]) for e in design["evaluations"]]
        batch = [{"venture": e["venture"], "judge": e["judge"], "persona": persona[e["judge"]],
                  "scores": {c: e[c] for c in ("concept", "business_model", "market", "written_work", "investor_interest")},
                  "summary": written[e["venture"]]["summary"], "attempt": tries["comments"].get(k, 1)}
                 for e, k in zip(design["evaluations"], keys)]
        comments = generated(commenter, commenter.run_batch(batch, workers=8))
        matches = real_term_matches(
            ["\n".join([w["name"], *w["team"], w["pitch"], w["description"], w["summary"]]) for w in written.values()]
            + ["\n".join(c["comments"].values()) for c in comments])
        if matches is None:
            check = "not run: the real records' term list is not on this machine"
            break
        bad_summaries = [v for v, m in zip(written, matches) if m]
        bad_comments = [k for k, m in zip(keys, matches[len(written):]) if m and k[0] not in bad_summaries]
        if not bad_summaries and not bad_comments:
            check = "passed: no generated text matches the real records' term list"
            break
        print(f"attempt {attempt}: {len(bad_summaries)} summaries and {len(bad_comments)} sets of comments match"
              " the real records' term list; writing them again", flush=True)
        for v in bad_summaries:
            tries["summary"][v] = tries["summary"].get(v, 1) + 1
        for k in bad_comments:
            tries["comments"][k] = tries["comments"].get(k, 1) + 1
    else:
        sys.exit(f"generated texts still match the real records' term list after {MAX_ATTEMPTS} attempts")
    spent = cost(concepter) + cost(writer) + cost(commenter)
    print(f"summaries and comments written; their calls cost ${spent:.2f}", flush=True)
    print(check, flush=True)

    rng = np.random.default_rng(YEAR)
    raw = SYNTHETIC / "raw" / str(YEAR)
    shutil.rmtree(raw, ignore_errors=True)  # the files of an earlier build
    for folder in ("PDF", "Word"):
        (raw / "R1" / folder).mkdir(parents=True, exist_ok=True)
    ids = {v["venture"]: identifier(rng) for v in ventures}
    advanced = set(design["advanced"])
    manifest, terms = [], set()
    wb = Workbook()
    apps = wb.active
    apps.title = "Worksheet"
    apps.append(APPLICATION_HEADERS)
    for v in ventures:
        w = written[v["venture"]]
        word = v["venture"] % 8 == 0
        file_name = f"{v['venture']:02d}_{slug(w['name']) or 'venture'}_executive_summary.{'docx' if word else 'pdf'}"
        path = raw / "R1" / ("Word" if word else "PDF") / file_name
        path.write_bytes(docx_bytes(w["name"], w["summary"]) if word else pdf_bytes(w["name"], w["summary"]))
        manifest.append({"year": YEAR, "round": 1, "doc_type": "exec_summary", "entry_identifier": ids[v["venture"]],
                         "file_name": file_name, "status": "downloaded", "path": str(path.relative_to(SYNTHETIC)),
                         "size_bytes": path.stat().st_size, "sha256": sha256_file(path), "drive_file_id": "", "platform_url": ""})
        lead = w["team"][0] if w["team"] else f"Founder {v['venture']}"
        terms |= {("venture", w["name"]), *(("person", t) for t in w["team"])}
        apps.append([w["name"], ids[v["venture"]], f"{YEAR}-01-{v['venture'] % 28 + 1:02d} 10:00", f"{YEAR}-02-01 12:00",
                     lead, f"founder{v['venture']:02d}@example.org", "Team Lead", "Yes",
                     "Yes" if v["venture"] in advanced else "No", "No", "A friend",
                     w["pitch"], w["description"], " | ".join(v["product_types"]), v["company_type"], " | ".join(v["fields"]),
                     " | ".join(v["milestones"]) or None, None, "Yes" if v["entity_formed"] else "No", v["entity_type"],
                     f"https://{slug(w['name'])}.example.com" if v["has_website"] else None,
                     *(["Yes"] * 12), "Accepted", file_name, "Not accepted", None])
    for i in range(1, 5):  # applications started and never submitted
        apps.append([f"Unsubmitted application {i}", identifier(rng), f"{YEAR}-01-{i + 10:02d} 09:00", None,
                     f"Applicant {i}", f"applicant{i}@example.org", "Team Lead", "Yes", "No", "No"])
    judging = wb.create_sheet("Worksheet 1")
    judging.append(JUDGING_HEADERS)
    means = {}
    for e in design["evaluations"]:
        means.setdefault(e["venture"], []).append(e["weighted"])
    means = {k: round(sum(x) / len(x), 6) for k, x in means.items()}
    rank = {m: i + 1 for i, m in enumerate(sorted(set(means.values()), reverse=True))}
    for e, c in zip(design["evaluations"], comments):
        c = c["comments"]
        terms.add(("person", f"Judge {e['judge']:02d}"))
        judging.append([rank[means[e["venture"]]], written[e["venture"]]["name"], ids[e["venture"]],
                        f"judge{e['judge']:02d}@example.org", f"Judge {e['judge']:02d}", c["concept"], e["concept"],
                        c["concept_score_comment"] or None, c["business_model"], e["business_model"], c["market"], e["market"],
                        e["written_work"], c["written_work"], e["investor_interest"], c["investor_interest"], e["weighted"]])
    buffer = io.BytesIO()
    wb.save(buffer)
    (raw / f"{YEAR} R1.xlsx").write_bytes(fixed_zip(buffer.getvalue()))

    (SYNTHETIC / "manifests").mkdir(parents=True, exist_ok=True)
    with open(SYNTHETIC / "manifests" / f"{YEAR}_documents.csv", "w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=list(manifest[0]))
        out.writeheader()
        out.writerows(manifest)
    (SYNTHETIC / "private").mkdir(parents=True, exist_ok=True)
    (SYNTHETIC / "private" / "sensitive_terms.tsv").write_text("".join(f"{c}\t{t}\n" for c, t in sorted(terms)))
    (SYNTHETIC / "synthetic.json").write_text(json.dumps({
        "year": YEAR, "seed": YEAR, "built": date.today().isoformat(),
        "generators": {c.contract.component: c.config_hash for c in (competition, concepter, writer, commenter)},
        "design": design_run.output_sha, "ventures": len(ventures), "judges": len(judges),
        "evaluations": len(design["evaluations"]), "advanced": len(advanced),
        "files": {"pdf": sum(m["file_name"].endswith(".pdf") for m in manifest),
                  "docx": sum(m["file_name"].endswith(".docx") for m in manifest)},
        "unsubmitted_applications": 4, "generation_cost_usd": round(spent, 2), "real_terms_check": check,
        "written_again": {"concepts": concept_attempt - 1, "summaries": sum(n > 1 for n in tries["summary"].values()),
                          "sets_of_comments": sum(n > 1 for n in tries["comments"].values()),
                          "why": "an earlier attempt matched the real records' sensitive-term list"}}, indent=1) + "\n")
    print(f"built: {len(manifest)} summaries, {len(ventures) + 4} applications, {len(design['evaluations'])} evaluations,"
          f" in {SYNTHETIC.relative_to(ROOT) if SYNTHETIC.is_relative_to(ROOT) else SYNTHETIC}")


# ---- Run -----------------------------------------------------------------

def run() -> None:
    """The whole pipeline on the synthetic competition, in the order it ran on
    2019: records, the judges' pilot and full run, then Study A."""
    use_synthetic_data()
    from . import extract, judge, profile, pseudonymize, study_a, tables

    pseudonymize.main(YEAR)
    extract.main(YEAR)
    tables.main(YEAR)
    profile.main(YEAR)
    texts = judge.summaries(YEAR)
    pilot = judge.pilot_entries(YEAR)
    judge.run_claude(YEAR, texts, pilot)
    judge.run_qwen(YEAR, texts, pilot)
    judge.report(YEAR)
    judge.run_claude(YEAR, texts, sorted(texts), label="full", workers=12, group=3)
    judge.run_qwen(YEAR, texts, sorted(texts), label="full", precheck=True)
    judge.full_report(YEAR)
    study_a.embed_check(YEAR)
    study_a.report(YEAR)
    print("the pipeline ran on the synthetic competition; its reports are in synthetic/data/reports/")


def publish_outputs(target: Path) -> int:
    """The synthetic competition's outputs that the public repository carries,
    copied into another data folder: the stored outputs of every component
    except the generators, with their provenance records, and the analysis
    tables. B1 carries over only the outputs of the components that call a model
    (the AI judges and the embedders), computes every other output again without
    calling a model, and compares each with the published one. The generators'
    outputs are left out: the repository holds the files they wrote, and their
    earlier attempts include texts that matched the real records' term list.
    The provenance records name no one: the person who ran each step is given
    as the authors. Returns the number of stored outputs."""
    from ..paths import COMPONENTS
    from ..store import Store
    from .study_b import carry_store

    components = sorted(d.name for d in COMPONENTS.iterdir()
                        if (d / "contract.yaml").exists() and not d.name.startswith("synthetic_"))
    entries = carry_store(SYNTHETIC, target, components)
    shutil.copytree(SYNTHETIC / "tables", target / "tables")
    store = Store(target / "store")
    for path in (target / "store" / "provenance").rglob("*.json"):
        record = store.get_record(path.parent.name, path.stem)
        record["prov:wasAssociatedWith"]["agent"] = PUBLISHED_AGENT
        store.put_record(path.parent.name, record)
    return entries


if __name__ == "__main__":
    {"build": build, "run": run}[sys.argv[1]]()
