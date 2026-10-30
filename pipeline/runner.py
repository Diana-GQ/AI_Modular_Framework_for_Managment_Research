"""Run a component from its contract.

The runner loads the contract, checks the inputs against the declared types,
computes the inputs hash and the configuration hash, and returns the stored
output if this configuration has already run on these inputs: outputs are never
regenerated silently. Otherwise it runs the component's code, checks the outputs
against the declared types, stores them and writes a provenance record.

A component's code (component.py) defines run(inputs, settings) -> dict and,
optionally, run_batch(list_of_inputs, settings) -> list[dict]. It may return a
"_details" entry (for example, the full request and response of a model call),
which is stored in the provenance record rather than in the output. A run that
raises an exception stores nothing, so a later run tries it again.
"""

import importlib.util
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from .contracts import Contract, TypeSpec, config_hash, load_contract
from .hashing import sha256_file, sha256_json
from .paths import COMPONENTS
from .provenance import make_record, now
from .store import Store, resolve


class ContractError(Exception):
    """An input or output does not match the component's contract."""


@dataclass
class RunResult:
    outputs: dict
    output_sha: str
    record_id: str
    cached: bool


@dataclass
class RunError:
    """A run in a batch that failed. Nothing was stored for it."""
    error: str


def _component_dir(component) -> Path:
    path = Path(component)
    return path if path.is_dir() else COMPONENTS / str(component)


def _load_module(component_dir: Path):
    spec = importlib.util.spec_from_file_location(f"components.{component_dir.name}", component_dir / "component.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_value(name: str, spec: TypeSpec, value, where: str) -> None:
    def fail(msg):
        raise ContractError(f"{where} '{name}': {msg}")

    if value is None:
        if spec.optional:
            return
        fail("missing value")
    kind = spec.kind
    if kind == "text" and not isinstance(value, str):
        fail("expected text")
    if kind == "boolean" and not isinstance(value, bool):
        fail("expected a boolean")
    if kind in ("integer", "number"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            fail(f"expected a {kind}")
        if kind == "integer" and not float(value).is_integer():
            fail("expected an integer")
        if spec.range and not (spec.range[0] <= value <= spec.range[1]):
            fail(f"{value} outside {spec.range}")
    if spec.values is not None and value not in spec.values:
        fail(f"{value!r} not among the allowed values")
    if kind == "vector" and not (isinstance(value, list) and all(isinstance(x, (int, float)) for x in value)):
        fail("expected a list of numbers")
    if kind == "record":
        if not isinstance(value, dict):
            fail("expected a record")
        missing = set(spec.fields or {}) - set(value)
        if missing:
            fail(f"missing fields {sorted(missing)}")
    if kind == "table":
        if not (isinstance(value, list) and all(isinstance(r, dict) for r in value)):
            fail("expected a list of rows")
        if spec.fields:
            for row in value:
                if set(row) != set(spec.fields):
                    fail(f"row columns differ from the declared ones: {sorted(set(row) ^ set(spec.fields))}")
    if kind in ("file", "matrix") and not (isinstance(value, dict) and {"path", "sha256"} <= set(value)):
        fail("expected a file reference with path and sha256")


def check_tools(contract: Contract) -> None:
    """Each pinned tool that is a Python package must be installed at its pinned
    version. Other tools (such as an operating-system command) are recorded only."""
    for tool, version in contract.pinned.tools.items():
        try:
            installed = metadata.version(tool)
        except metadata.PackageNotFoundError:
            continue
        if installed != str(version):
            raise ContractError(f"{contract.component}: {tool} {installed} is installed; the contract pins {version}")


def check_inputs(contract: Contract, inputs: dict) -> None:
    unknown = set(inputs) - set(contract.typed.inputs)
    if unknown:
        raise ContractError(f"{contract.component}: undeclared inputs {sorted(unknown)}")
    for name, spec in contract.typed.inputs.items():
        _check_value(name, spec, inputs.get(name), f"{contract.component} input")


def check_outputs(contract: Contract, outputs: dict) -> None:
    unknown = set(outputs) - set(contract.typed.outputs)
    if unknown:
        raise ContractError(f"{contract.component}: undeclared outputs {sorted(unknown)}")
    for name, spec in contract.typed.outputs.items():
        _check_value(name, spec, outputs.get(name), f"{contract.component} output")


def _input_hashes(contract: Contract, inputs: dict) -> dict:
    """Files are identified by their content hash, not their path; the hash
    given with a file is checked against its content."""
    hashes = {}
    for name, value in inputs.items():
        spec = contract.typed.inputs[name]
        if spec.kind in ("file", "matrix") and value:
            if sha256_file(resolve(value)) != value["sha256"]:
                raise ContractError(f"{contract.component} input '{name}': the file does not match its SHA-256")
            hashes[name] = value["sha256"]
        else:
            hashes[name] = sha256_json(value)
    return hashes


class Component:
    """A component loaded once and run many times."""

    def __init__(self, component, store: Store | None = None):
        self.dir = _component_dir(component)
        self.contract = load_contract(self.dir)
        self.config_hash = config_hash(self.contract, self.dir)
        # The code sees the pinned settings, and the pinned model under "model".
        self.settings = dict(self.contract.pinned.settings)
        if self.contract.pinned.model:
            if "model" in self.settings:
                raise ContractError(f"{self.contract.component}: 'model' belongs in pinned.model, not in settings")
            self.settings["model"] = self.contract.pinned.model
        self.store = store or Store()
        self._module = None

    @property
    def module(self):
        """The component's code, loaded when it first has to run."""
        if self._module is None:
            check_tools(self.contract)
            self._module = _load_module(self.dir)
        return self._module

    def _prepare(self, inputs: dict):
        check_inputs(self.contract, inputs)
        input_hashes = _input_hashes(self.contract, inputs)
        return input_hashes, sha256_json(input_hashes)

    def _save(self, inputs_hash, input_hashes, outputs, started, ended, batch_id, rerun) -> RunResult:
        details = outputs.pop("_details", None)
        check_outputs(self.contract, outputs)
        output_sha = self.store.put(outputs)
        record = make_record(contract=self.contract, config_hash=self.config_hash, inputs_hash=inputs_hash,
                             input_hashes=input_hashes, output_sha=output_sha, started=started, ended=ended,
                             batch_id=batch_id, rerun=rerun, details=details)
        self.store.put_record(self.contract.component, record)
        self.store.record_run(self.contract.component, self.config_hash, inputs_hash, output_sha, record["id"])
        # Returned as stored, so that a new output and a reused one are the same object, keys in the same order.
        return RunResult(self.store.get(output_sha), output_sha, record["id"], cached=False)

    def _lookup(self, inputs_hash: str) -> RunResult | None:
        entry = self.store.lookup(self.contract.component, self.config_hash, inputs_hash)
        if entry is None:
            return None
        return RunResult(self.store.get(entry["output"]), entry["output"], entry["record"], cached=True)

    def cached(self, inputs: dict) -> RunResult | None:
        return self._lookup(self._prepare(inputs)[1])

    def run(self, inputs: dict, *, rerun: bool = False) -> RunResult:
        input_hashes, inputs_hash = self._prepare(inputs)
        if not rerun:
            hit = self._lookup(inputs_hash)
            if hit:
                return hit
        started = now()
        outputs = dict(self.module.run(inputs, self.settings))
        return self._save(inputs_hash, input_hashes, outputs, started, now(), None, rerun)

    def run_batch(self, batch: list[dict], *, rerun: bool = False, workers: int = 1,
                  progress=None) -> list[RunResult | RunError]:
        """Run many inputs, executing only those without a stored output (unless
        rerun) and identical inputs once. Uses the component's run_batch when it
        has one; otherwise runs the inputs in up to `workers` threads. Each
        output is stored as soon as it arrives; a failed run gives a RunError in
        its place. `progress`, if given, is called after each run."""
        prepared = [self._prepare(inputs) for inputs in batch]
        results: list[RunResult | RunError | None] = [None] * len(batch)
        pending: dict[str, list[int]] = {}
        for i, (_, inputs_hash) in enumerate(prepared):
            hit = None if rerun else self._lookup(inputs_hash)
            if hit:
                results[i] = hit
            else:
                pending.setdefault(inputs_hash, []).append(i)
        if not pending:
            return results
        batch_id = f"urn:uuid:{uuid.uuid4()}"
        first = [indices[0] for indices in pending.values()]

        def finish(i, outputs, started, ended):
            input_hashes, inputs_hash = prepared[i]
            result = self._save(inputs_hash, input_hashes, dict(outputs), started, ended, batch_id, rerun)
            for j in pending[inputs_hash]:
                results[j] = result

        def fail(i, error):
            for j in pending[prepared[i][1]]:
                results[j] = RunError(f"{type(error).__name__}: {error}")

        if hasattr(self.module, "run_batch"):
            started = now()
            outputs = self.module.run_batch([batch[i] for i in first], self.settings)
            ended = now()
            for i, out in zip(first, outputs):
                finish(i, out, started, ended)
            return results

        def one(i):
            started = now()
            out = self.module.run(batch[i], self.settings)
            return out, started, now()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(one, i): i for i in first}
            for future in as_completed(futures):
                i = futures[future]
                try:
                    finish(i, *future.result())
                except Exception as e:  # noqa: BLE001 - recorded in the results
                    fail(i, e)
                if progress:
                    progress()
        return results

def run(component, inputs: dict, *, rerun: bool = False, store: Store | None = None) -> RunResult:
    return Component(component, store).run(inputs, rerun=rerun)
