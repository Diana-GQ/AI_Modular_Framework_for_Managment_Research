"""What the stages share: the year's files and where reports go."""

import csv
import json
from pathlib import Path

from ..hashing import canonical_json, sha256_file
from ..paths import data_dir


def file_ref(path: Path) -> dict:
    return {"path": str(path), "sha256": sha256_file(path)}


def workbook(year: int) -> Path:
    found = sorted((data_dir() / "raw" / str(year)).glob("*.xlsx"))
    if len(found) != 1:
        raise FileNotFoundError(f"expected one export workbook for {year}, found {len(found)}")
    return found[0]


def summaries(year: int) -> list[dict]:
    """The year's downloaded executive summaries, from its manifest, with the
    path made absolute and the checksum verified."""
    with open(data_dir() / "manifests" / f"{year}_documents.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["doc_type"] == "exec_summary" and r["status"] == "downloaded"]
    for r in rows:
        r["path"] = str(data_dir() / r["path"])
        r["file_type"] = Path(r["path"]).suffix.lower().lstrip(".")
    return rows


def reports_dir() -> Path:
    path = data_dir() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_report(name: str, report: dict) -> Path:
    path = reports_dir() / name
    path.write_text(json.dumps(json.loads(canonical_json(report)), indent=1, ensure_ascii=False) + "\n")
    return path
