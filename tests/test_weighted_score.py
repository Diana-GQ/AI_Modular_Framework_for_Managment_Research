import importlib.util

import pytest

from pipeline.contracts import load_contract
from pipeline.paths import COMPONENTS

spec = importlib.util.spec_from_file_location("ws", COMPONENTS / "weighted_score" / "component.py")
ws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ws)
SETTINGS = load_contract(COMPONENTS / "weighted_score").pinned.settings


@pytest.mark.parametrize("scores,expected", [
    (dict.fromkeys(ws.CRITERIA, 10), 10.0),
    (dict.fromkeys(ws.CRITERIA, 1), 1.0),
    ({"concept": 7, "business_model": 6, "market": 8, "written_work": 5, "investor_interest": 6}, 6.5),
    ({"concept": 10, "business_model": 1, "market": 1, "written_work": 1, "investor_interest": 1}, 2.8),
])
def test_formula(scores, expected):
    assert ws.run({"scores": scores}, SETTINGS)["weighted_score"] == pytest.approx(expected)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        ws.run({"scores": dict.fromkeys(ws.CRITERIA, 5)}, {"weights": dict.fromkeys(ws.CRITERIA, 0.5)})
