import pytest

from pipeline.checks import MethodError, assert_comparable, assert_ready_for_inference
from pipeline.contracts import Check, Contract, TypeSpec, load_contract
from pipeline.paths import COMPONENTS


def vector(**kw):
    base = dict(kind="vector", meaning="embedding", model="model-a@1", instruction="assess the market", postprocessing="whitened")
    base.update(kw)
    return TypeSpec(**base)


def test_vectors_of_the_same_type_are_comparable():
    assert_comparable(vector(), vector())


@pytest.mark.parametrize("field,value", [("model", "model-b@1"), ("instruction", "assess the team"), ("postprocessing", "raw")])
def test_vectors_of_different_types_are_refused(field, value):
    with pytest.raises(MethodError):
        assert_comparable(vector(), vector(**{field: value}))


def test_non_vectors_are_refused():
    with pytest.raises(MethodError):
        assert_comparable(vector(), TypeSpec(kind="number", meaning="score"))


def stochastic_contract(status="validated", checks=()):
    data = load_contract(COMPONENTS / "weighted_score").model_dump()
    data.update(deterministic=False)
    data["validated"] = {"status": status, "checks": list(checks)}
    return Contract.model_validate(data)


def test_deterministic_validated_component_may_enter_inference():
    assert_ready_for_inference(load_contract(COMPONENTS / "weighted_score"))


def test_provisional_component_is_refused():
    with pytest.raises(MethodError):
        assert_ready_for_inference(stochastic_contract(status="provisional"))


def test_stochastic_component_without_reliability_is_refused():
    with pytest.raises(MethodError):
        assert_ready_for_inference(stochastic_contract(checks=[{"name": "tests", "kind": "unit_tests", "result": "pass"}]))


def test_stochastic_component_with_reliability_may_enter_inference():
    assert_ready_for_inference(stochastic_contract(checks=[{"name": "five runs", "kind": "reliability", "result": "ICC 0.9"}]))
