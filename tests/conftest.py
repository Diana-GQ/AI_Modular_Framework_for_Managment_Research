import pytest


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    """Every test writes to its own temporary data folder, never to data/."""
    monkeypatch.setenv("COMPAI_DATA", str(tmp_path / "data"))
    return tmp_path / "data"
