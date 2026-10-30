"""Plan tasks 2.3 and 2.4: build a year's four analysis tables and check them
for identifying terms.

    uv run python -m pipeline.stages.tables 2019

Runs the records tables component on the export workbook, the private key and
the text extractor's outputs, and writes the tables to data/tables/<year>/ as
Parquet files, with tables.json pointing to the stored output and its
provenance record. Then runs the sensitive-term check on every cell: code and
category columns must contain no listed term and no email address. Free-text
columns (summaries, feedback, the form's written answers) necessarily name
ventures and people; for them the report gives counts only.
"""

import json
import sys
from collections import Counter

import pandas as pd

from .. import pseudonyms
from ..paths import ROOT, data_dir
from ..runner import Component
from .common import file_ref, workbook, write_report
from .extract import extractions

FREE_TEXT = {"text", "pitch", "description", "product_type", "fields", "milestones", "milestones_other", "entity_type"}


def build(year: int):
    rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in extractions(year)]
    inputs = {"year": year, "workbook": file_ref(workbook(year)), "key": file_ref(pseudonyms.key_path()),
              "extractions": rows}
    return Component("records_tables").run(inputs)


def export(year: int, result) -> dict[str, pd.DataFrame]:
    folder = data_dir() / "tables" / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    frames = {}
    spec = Component("records_tables").contract.typed.outputs
    for name, rows in result.outputs.items():
        # Columns in the order the contract declares them, whatever the order of the stored keys.
        frames[name] = pd.DataFrame(rows, columns=list(spec[name].fields))
        frames[name].to_parquet(folder / f"{name}.parquet", index=False)
    (folder / "tables.json").write_text(json.dumps({
        "component": "records_tables", "output": result.output_sha, "provenance_record": result.record_id,
        "tables": {name: len(rows) for name, rows in result.outputs.items()}}, indent=1) + "\n")
    return frames


def sensitive_check(frames: dict[str, pd.DataFrame]) -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_sensitive

    # The terms of the data being checked: the real records', or the synthetic competition's.
    patterns, allow = check_sensitive.load_patterns(data_dir() / "private" / "sensitive_terms.tsv",
                                                    data_dir() / "private" / "sensitive_allow.txt")

    def hits(value) -> Counter:
        found = Counter()
        if not isinstance(value, str):
            return found
        for rx in allow:
            value = rx.sub(lambda m: " " * len(m.group(0)), value)
        found.update("email" for _ in check_sensitive.EMAIL.finditer(value))
        for category, _, rx in patterns:
            if rx.search(value):
                found[category] += 1
        return found

    report = {"terms": len(patterns), "coded_columns": {}, "free_text_columns": {}}
    for name, frame in frames.items():
        for column in frame.columns:
            counts, cells = Counter(), 0
            for value in frame[column]:
                h = hits(value)
                counts += h
                cells += bool(h)
            group = "free_text_columns" if column in FREE_TEXT else "coded_columns"
            report[group][f"{name}.{column}"] = {"cells_with_terms": cells, "by_category": dict(counts)}
    report["passed"] = all(v["cells_with_terms"] == 0 for v in report["coded_columns"].values())
    return report


def main(year: int) -> None:
    result = build(year)
    frames = export(year, result)
    print(f"tables for {year}: " + ", ".join(f"{n} {len(f)}" for n, f in frames.items())
          + (" (stored output reused)" if result.cached else ""))
    report = sensitive_check(frames)
    write_report(f"{year}_sensitive_check.json", report)
    free = {k: v["cells_with_terms"] for k, v in report["free_text_columns"].items() if v["cells_with_terms"]}
    print(f"sensitive-term check of code and category columns: {'passed' if report['passed'] else 'FAILED'}")
    print(f"free-text cells naming a listed term (expected): {free}")
    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main(int(sys.argv[1]))
