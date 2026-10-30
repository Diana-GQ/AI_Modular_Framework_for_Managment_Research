"""Project locations. COMPAI_DATA overrides the data folder (used by tests)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS = ROOT / "components"


def data_dir() -> Path:
    return Path(os.environ.get("COMPAI_DATA", ROOT / "data"))


def store_dir() -> Path:
    return data_dir() / "store"
