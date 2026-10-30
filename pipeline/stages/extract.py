"""Plan task 2.2: extract the text of a year's executive summaries.

    uv run python -m pipeline.stages.extract 2019

Runs the text extractor on every downloaded summary in the year's manifest.
Where the authors' earlier extraction exists (data/raw/<year>/<year>_R1_Output.json,
with the PDF and .docx files), compares the two, word by word.
Then prepares the authors' visual check of 20 extractions: the texts go to
data/reports/<year>_spot_check/, named by entry code, and the list linking
codes to files goes to data/private/, because file names name the ventures.
"""

import csv
import json
import os
import random
import re
import statistics
import sys
import unicodedata
from collections import Counter

from .. import pseudonyms
from ..paths import data_dir
from ..runner import Component
from .common import file_ref, reports_dir, summaries, write_report

SPOT_CHECK = 20


def extractions(year: int) -> list[dict]:
    """The extractor's output for each summary, running it only where no
    output is stored yet. Rows follow the records tables' 'extractions' input."""
    rows = summaries(year)
    results = Component("text_extractor").run_batch([{"file": file_ref(r["path"])} for r in rows])
    return [{"entry_identifier": r["entry_identifier"], "file_type": r["file_type"], "sha256": r["sha256"],
             **{k: res.outputs[k] for k in ("text", "pages", "words", "method", "needs_ocr")},
             "extraction": res.output_sha, "_file": r["file_name"], "_path": r["path"]}
            for r, res in zip(rows, results)]


def file_key(name: str) -> str:
    """File names compared loosely, since the two listings differ in accents and punctuation."""
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", name).lower())


def words(text: str) -> Counter:
    return Counter(re.findall(r"[a-z0-9]+", text.lower()))


def overlap(a: Counter, b: Counter) -> float:
    """The share of a's words found in b, counting repeats."""
    total = sum(a.values())
    return sum((a & b).values()) / total if total else 0.0


def main(year: int) -> None:
    rows = extractions(year)
    key = pseudonyms.load()
    for r in rows:
        r["entry"] = pseudonyms.code(key, "entry", r["entry_identifier"])

    report = {"year": year, "summaries": len(rows), "by_type": dict(Counter(r["file_type"] for r in rows)),
              "needs_ocr": sum(r["needs_ocr"] for r in rows),
              "pages": dict(sorted(Counter(r["pages"] for r in rows if r["pages"] is not None).items())),
              "words": {"min": min(r["words"] for r in rows), "median": statistics.median(r["words"] for r in rows),
                        "max": max(r["words"] for r in rows)}}

    earlier_path = data_dir() / "raw" / str(year) / f"{year}_R1_Output.json"
    low = []
    if earlier_path.exists():
        parts = json.loads(earlier_path.read_text())["Extracted_Text"]
        earlier = [v for part in parts.values() for v in part.values()]
        exact = {unicodedata.normalize("NFC", v["File Name"]): v for v in earlier}
        loose = {file_key(v["File Name"]): v for v in earlier}
        unique = {k for k, n in Counter(file_key(v["File Name"]) for v in earlier).items() if n == 1}
        unique &= {k for k, n in Counter(file_key(r["_file"]) for r in rows).items() if n == 1}
        compared = []
        for r in rows:
            e = exact.get(unicodedata.normalize("NFC", r["_file"]))
            if e is None and file_key(r["_file"]) in unique:
                e = loose[file_key(r["_file"])]
            if e is None:
                continue
            ours, theirs = words(r["text"]), words(e["Extracted Text"])
            r["agreement"] = min(overlap(ours, theirs), overlap(theirs, ours))
            compared.append({"entry": r["entry"], "file_type": r["file_type"], "agreement": round(r["agreement"], 4),
                             "same_pages": r["pages"] == e["Total Pages"] if r["file_type"] == "pdf" else None})
        values = [c["agreement"] for c in compared]
        low = sorted((c for c in compared if c["agreement"] < 0.95), key=lambda c: c["agreement"])
        report["earlier_extraction"] = {
            "earlier_files": len(earlier), "compared": len(compared),
            "compared_by_type": dict(Counter(c["file_type"] for c in compared)),
            "same_page_count_pdf": sum(bool(c["same_pages"]) for c in compared),
            "agreement": {"min": min(values), "median": statistics.median(values),
                          "below_0.95": len(low)},
            "below_0.95": low,
            "metric": "the smaller of the two shares of each extraction's words found in the other, counting repeats",
        }

    # The visual check: every summary below 0.95 (up to 10), every summary not
    # compared, up to three Word files, and a random draw of the rest.
    rng = random.Random(year)
    flagged = {c["entry"] for c in low[:10]}
    chosen = sorted((r for r in rows if r["entry"] in flagged or "agreement" not in r), key=lambda r: r["entry"])
    word_files = sorted((r for r in rows if r["file_type"] != "pdf" and r not in chosen), key=lambda r: r["entry"])
    chosen += rng.sample(word_files, max(0, min(3 - sum(r["file_type"] != "pdf" for r in chosen), len(word_files))))
    rest = sorted((r for r in rows if r not in chosen), key=lambda r: r["entry"])
    chosen = chosen[:SPOT_CHECK] + rng.sample(rest, max(0, SPOT_CHECK - len(chosen)))
    folder = reports_dir() / f"{year}_spot_check"
    folder.mkdir(exist_ok=True)
    for r in chosen:
        (folder / f"{r['entry']}.txt").write_text(r["text"] + "\n")
    with open(data_dir() / "private" / f"{year}_spot_check_files.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["entry", "file"])
        writer.writerows(sorted((r["entry"], r["_path"]) for r in chosen))
    os.chmod(data_dir() / "private" / f"{year}_spot_check_files.csv", 0o600)
    report["spot_check"] = sorted(r["entry"] for r in chosen)
    path = write_report(f"{year}_extraction_check.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("spot_check",)}, indent=1, default=str)
          .replace(json.dumps(low, indent=1), f"[{len(low)} entries]"))
    print(f"report: {path.relative_to(data_dir().parent)}; spot-check texts: {folder.relative_to(data_dir().parent)}")


if __name__ == "__main__":
    main(int(sys.argv[1]))
