import json
import shutil
from pathlib import Path

import pytest
import yaml

from pipeline.contracts import config_hash, load_contract
from pipeline.paths import COMPONENTS
from pipeline.runner import Component, ContractError
from pipeline.store import Store

SCORES = {"concept": 7, "business_model": 6, "market": 8, "written_work": 5, "investor_interest": 6}


def test_every_contract_validates():
    for contract_file in COMPONENTS.glob("*/contract.yaml"):
        load_contract(contract_file.parent)


def copy_component(tmp_path, name="weighted_score") -> Path:
    target = tmp_path / "components" / name
    shutil.copytree(COMPONENTS / name, target)
    return target


def test_config_hash_is_stable_and_changes_with_settings(tmp_path):
    comp = copy_component(tmp_path)
    first = config_hash(load_contract(comp), comp)
    assert first == config_hash(load_contract(comp), comp)
    data = yaml.safe_load((comp / "contract.yaml").read_text())
    data["pinned"]["settings"]["weights"]["concept"] = 0.25
    data["pinned"]["settings"]["weights"]["market"] = 0.15
    (comp / "contract.yaml").write_text(yaml.safe_dump(data))
    assert config_hash(load_contract(comp), comp) != first


def test_config_hash_changes_with_code(tmp_path):
    comp = copy_component(tmp_path)
    first = config_hash(load_contract(comp), comp)
    (comp / "component.py").write_text((comp / "component.py").read_text() + "\n# changed\n")
    assert config_hash(load_contract(comp), comp) != first


def test_store_is_content_addressed(tmp_path):
    store = Store(tmp_path / "store")
    a = store.put({"b": 1, "a": 2})
    assert a == store.put({"a": 2, "b": 1})
    assert store.get(a) == {"a": 2, "b": 1}


def test_run_stores_output_and_provenance_and_never_regenerates(tmp_path):
    store = Store(tmp_path / "store")
    comp = Component("weighted_score", store)
    first = comp.run({"scores": SCORES})
    assert not first.cached and first.outputs == {"weighted_score": 6.5}
    record = store.get_record("weighted_score", first.record_id)
    assert record["component"]["config_hash"] == comp.config_hash
    assert record["prov:generated"][0]["entity"] == f"sha256:{first.output_sha}"
    second = comp.run({"scores": SCORES})
    assert second.cached and second.record_id == first.record_id
    again = comp.run({"scores": SCORES}, rerun=True)
    assert not again.cached
    entry = store.lookup("weighted_score", comp.config_hash, comp._prepare({"scores": SCORES})[1])
    assert entry["record"] == first.record_id and entry["reruns"][0]["record"] == again.record_id


def test_run_batch_runs_only_what_is_missing(tmp_path):
    store = Store(tmp_path / "store")
    comp = Component("weighted_score", store)
    comp.run({"scores": SCORES})
    other = dict(SCORES, concept=9)
    results = comp.run_batch([{"scores": SCORES}, {"scores": other}])
    assert [r.cached for r in results] == [True, False]


def test_inputs_and_outputs_are_checked_against_the_contract(tmp_path):
    comp = Component("weighted_score", Store(tmp_path / "store"))
    with pytest.raises(ContractError):
        comp.run({"scores": {"concept": 7}})          # missing fields
    with pytest.raises(ContractError):
        comp.run({"scores": SCORES, "extra": 1})       # undeclared input
    bad = {k: 0 for k in SCORES}                       # weighted score 0 is outside [1, 10]
    with pytest.raises(ContractError):
        comp.run({"scores": bad})


def test_file_input_must_match_its_hash(tmp_path):
    from tests import synthetic

    path = synthetic.docx(tmp_path / "a.docx", ["Some text"])
    ref = synthetic.file_ref(path)
    synthetic.docx(path, ["Other text"])
    with pytest.raises(ContractError):
        Component("text_extractor").run({"file": ref})


def test_pinned_package_versions_are_enforced(tmp_path):
    comp = copy_component(tmp_path)
    data = yaml.safe_load((comp / "contract.yaml").read_text())
    data["pinned"]["tools"] = {"pyyaml": "0.0.1", "some-system-command": "any"}
    (comp / "contract.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(ContractError, match="pins 0.0.1"):
        Component(comp).run({"scores": SCORES})


def test_table_columns_are_checked(tmp_path):
    from pipeline.runner import check_outputs

    contract = load_contract(COMPONENTS / "records_tables")
    with pytest.raises(ContractError, match="columns differ"):
        check_outputs(contract, {"entries": [], "documents": [], "evaluations": [], "judges": [{"judge": "J-1", "name": "x"}]})


def test_batch_runs_identical_inputs_once_and_reports_failures(tmp_path):
    from pipeline.runner import RunError

    comp = copy_component(tmp_path)
    code = (comp / "component.py").read_text()
    code += '''

CALLS = []


def _run(inputs, settings):
    CALLS.append(inputs)
    if inputs["scores"]["concept"] == 1:
        raise RuntimeError("service unavailable")
    return run(inputs, settings)
'''
    code = code.replace("def run(", "def run_original(", 1).replace("return run(inputs, settings)", "return run_original(inputs, settings)")
    code = code.replace("def _run(", "def run(")
    (comp / "component.py").write_text(code)
    c = Component(comp)
    bad = dict(SCORES, concept=1)
    results = c.run_batch([{"scores": SCORES}, {"scores": SCORES}, {"scores": bad}], workers=3)
    assert len(c.module.CALLS) == 2
    assert results[0] is results[1] and not results[0].cached
    assert isinstance(results[2], RunError) and "service unavailable" in results[2].error
    assert c.cached({"scores": bad}) is None


def test_a_new_output_is_returned_as_stored(tmp_path):
    """A new output and the same output reused are the same object, keys in the same order,
    so that nothing downstream depends on whether an output was just computed."""
    comp_dir = tmp_path / "components" / "toy"
    comp_dir.mkdir(parents=True)
    (comp_dir / "component.py").write_text(
        "def run(inputs, settings):\n    return {'zeta': {'y': inputs['n'], 'x': 2}, 'alpha': 1}\n")
    (comp_dir / "contract.yaml").write_text(yaml.safe_dump({
        "component": "toy", "version": "1.0.0", "role": "aggregator", "deterministic": True, "description": "A test.",
        "typed": {"inputs": {"n": {"kind": "integer", "meaning": "A number"}},
                  "outputs": {"zeta": {"kind": "json", "meaning": "A record"}, "alpha": {"kind": "integer", "meaning": "One"}}},
        "pinned": {"code": ["component.py"]}, "persisted": {"key": "inputs_hash+config_hash", "regenerate": "never"},
        "validated": {"status": "provisional", "checks": []}, "card": "card.md"}))
    comp = Component(comp_dir, Store(tmp_path / "store"))
    first, again = comp.run({"n": 1}), comp.run({"n": 1})
    assert not first.cached and again.cached
    assert first.outputs == again.outputs
    assert list(first.outputs) == list(again.outputs) == ["alpha", "zeta"] and list(first.outputs["zeta"]) == ["x", "y"]


def test_frozen_components_are_unchanged():
    """The pipeline is frozen (task 5.6): changing a component means a new
    version, recorded on its card, and the frozen list recorded again."""
    from pipeline import freeze

    assert freeze.differences() == []


def test_every_contract_states_its_four_parts(tmp_path):
    """A contract without its persisted section does not load."""
    comp = copy_component(tmp_path)
    data = yaml.safe_load((comp / "contract.yaml").read_text())
    assert data["persisted"] == {"key": "inputs_hash+config_hash", "regenerate": "never"}
    del data["persisted"]
    (comp / "contract.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(Exception):
        load_contract(comp)
