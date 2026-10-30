"""Codes in place of the identities of entries and judges (design, Section 1.5).

The key that links codes to identities is data/private/code_key.csv, kept apart
from the analysis tables. Codes are random: "E-" or "J-" and six hexadecimal
digits. A code is assigned once and then reused, so an entry or a judge seen
again, in another year, keeps its code. Entries are identified by the
platform's entry identifier, judges by their email address in lower case.
"""

import csv
import os
import secrets
from pathlib import Path

from .paths import data_dir

PREFIX = {"entry": "E", "judge": "J"}
FIELDS = ["kind", "identifier", "code", "first_year"]


def key_path() -> Path:
    return data_dir() / "private" / "code_key.csv"


def normalize(kind: str, identifier) -> str:
    text = str(identifier).strip()
    return text.lower() if kind == "judge" else text


def load(path: Path | None = None) -> dict[tuple[str, str], str]:
    """{(kind, identifier): code}"""
    path = Path(path or key_path())
    if not path.exists():
        return {}
    with open(path, newline="") as f:
        return {(r["kind"], r["identifier"]): r["code"] for r in csv.DictReader(f)}


def assign(kind: str, identifiers, year: int, path: Path | None = None) -> int:
    """Give a new code to each identifier that has none. Returns how many were added."""
    path = Path(path or key_path())
    rows = []
    if path.exists():
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    known = {(r["kind"], r["identifier"]) for r in rows}
    used = {r["code"] for r in rows}
    added = 0
    for identifier in identifiers:
        identifier = normalize(kind, identifier)
        if not identifier or (kind, identifier) in known:
            continue
        code = f"{PREFIX[kind]}-{secrets.token_hex(3)}"
        while code in used:
            code = f"{PREFIX[kind]}-{secrets.token_hex(3)}"
        rows.append({"kind": kind, "identifier": identifier, "code": code, "first_year": str(year)})
        known.add((kind, identifier))
        used.add(code)
        added += 1
    if added:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    return added


def code(key: dict, kind: str, identifier) -> str:
    try:
        return key[(kind, normalize(kind, identifier))]
    except KeyError:
        raise KeyError(f"no code for this {kind}; run the pseudonymize stage first") from None
