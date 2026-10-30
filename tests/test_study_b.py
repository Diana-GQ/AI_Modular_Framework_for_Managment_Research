import json
import sys

from pipeline.hashing import canonical_json, sha256_bytes
from pipeline.paths import ROOT
from pipeline.stages import study_b

sys.path.insert(0, str(ROOT / "scripts"))
import check_sensitive  # noqa: E402


def test_numerically_equal_tells_rounding_from_difference():
    assert study_b.numerically_equal({"a": [1.0, "x"], "n": 3}, {"a": [1.0 + 1e-15, "x"], "n": 3})
    assert not study_b.numerically_equal({"a": 1.0}, {"a": 1.0001})
    assert study_b.numerically_equal({"a": 1.0}, {"a": 1.000001}, rel=1e-5)
    assert not study_b.numerically_equal({"n": 3}, {"n": 4}) and not study_b.numerically_equal(["x"], ["y"])
    assert study_b.numerically_equal(float("nan"), float("nan"))


def store_output(root, component, key, obj):
    text = canonical_json(obj)
    sha = sha256_bytes(text.encode())
    (root / "store" / "objects" / sha[:2]).mkdir(parents=True, exist_ok=True)
    (root / "store" / "objects" / sha[:2] / f"{sha}.json").write_text(text)
    index = root / "store" / "index" / component / "config"
    index.mkdir(parents=True, exist_ok=True)
    (index / f"{key}.json").write_text(json.dumps({"output": sha, "record": "r", "reruns": []}))


def test_comparison_uses_the_precision_a_contract_declares(tmp_path):
    original, fresh = tmp_path / "original", tmp_path / "fresh"
    # The human benchmark declares a precision of 1e-5; the weighted score declares none.
    for root, value in ((original, 0.25), (fresh, 0.25 * (1 + 1e-7))):
        store_output(root, "human_benchmark", "a", {"share": value})
        store_output(root, "weighted_score", "a", {"weighted_score": value})
        store_output(root, "weighted_score", "b", {"weighted_score": 6.5})
    found = study_b.compare_store(original, fresh, carried=[])
    assert found["human_benchmark"]["within_declared_tolerance"] == 1
    assert found["weighted_score"]["different"] == 1 and found["weighted_score"]["identical"] == 1


def test_example_addresses_are_not_flagged_but_real_looking_ones_are(capsys):
    assert check_sensitive.scan("t", "judge01@example.org, x@mail.example.com", [], [], False) == 0
    # Built at run time, so that this file holds no address the check would flag.
    assert check_sensitive.scan("t", "someone" + "@mail.test", [], [], False) == 1


def test_term_lists_can_come_from_another_dataset(tmp_path):
    terms = tmp_path / "terms.tsv"
    terms.write_text("venture\tGreenlight Commute\n")
    patterns, allow = check_sensitive.load_patterns(terms, tmp_path / "none.txt")
    assert [t for _, t, _ in patterns] == ["Greenlight Commute"] and allow == []
    assert check_sensitive.scan("t", "We are Greenlight  Commute.", patterns, allow, False) == 1


def test_outputs_missing_from_the_original_are_reported_not_fatal(tmp_path):
    import pandas as pd

    original, fresh = tmp_path / "original", tmp_path / "fresh"
    (fresh / "tables" / "2000").mkdir(parents=True)
    pd.DataFrame({"entry": ["E001"]}).to_parquet(fresh / "tables" / "2000" / "entries.parquet")
    (fresh / "reports").mkdir()
    (fresh / "reports" / "2000_profile.json").write_text("{}")
    found = study_b.compare_outputs(original, fresh, 2000)
    assert found["tables"]["entries"] == "not in original" and found["tables"]["judges"] == "missing"
    assert found["reports"]["2000_profile.json"] == "not in original"
    assert found["reports"]["2000_pilot.json"] == "missing"
