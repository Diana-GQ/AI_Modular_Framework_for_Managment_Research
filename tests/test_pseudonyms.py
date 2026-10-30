import re

import pytest

from pipeline import pseudonyms


def test_codes_are_random_stable_and_private(tmp_path):
    path = tmp_path / "private" / "code_key.csv"
    assert pseudonyms.assign("entry", ["a1", "b2", "a1", " b2 "], 2019, path) == 2
    assert pseudonyms.assign("judge", ["Judge-One", "judge-one "], 2019, path) == 1
    key = pseudonyms.load(path)
    assert set(key) == {("entry", "a1"), ("entry", "b2"), ("judge", "judge-one")}
    assert all(re.fullmatch(r"[EJ]-[0-9a-f]{6}", c) for c in key.values())
    assert len(set(key.values())) == 3
    assert path.stat().st_mode & 0o077 == 0
    # A later year reuses existing codes and adds only new ones.
    assert pseudonyms.assign("entry", ["a1", "c3"], 2020, path) == 1
    later = pseudonyms.load(path)
    assert later[("entry", "a1")] == key[("entry", "a1")]
    assert pseudonyms.code(later, "judge", " JUDGE-ONE") == key[("judge", "judge-one")]


def test_unknown_identity(tmp_path):
    with pytest.raises(KeyError):
        pseudonyms.code({}, "entry", "zz")
