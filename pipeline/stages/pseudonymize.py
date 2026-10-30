"""Plan task 2.3: give every entry and judge of a year a code.

    uv run python -m pipeline.stages.pseudonymize 2019

Adds the year's new identities to the private key, data/private/code_key.csv,
and leaves existing codes unchanged.
"""

import sys

from .. import pseudonyms
from ..runner import Component
from .common import workbook


def main(year: int) -> None:
    tables = Component("records_tables")
    applications, judging = tables.module.read(str(workbook(year)), tables.settings)
    entries = [r["entry_identifier"] for r in applications] + [r["entry_identifier"] for r in judging]
    added_entries = pseudonyms.assign("entry", entries, year)
    added_judges = pseudonyms.assign("judge", [r["judge_email"] for r in judging], year)
    key = pseudonyms.load()
    print(f"{year}: {added_entries} new entry codes and {added_judges} new judge codes;"
          f" the key holds {sum(k == 'entry' for k, _ in key)} entries and {sum(k == 'judge' for k, _ in key)} judges")


if __name__ == "__main__":
    main(int(sys.argv[1]))
