"""The contract schema, its loader and the configuration hash.

A contract has one section per property of the framework's Section 3: typed,
pinned, persisted and validated, plus a pointer to the component's card. The
configuration hash fingerprints everything that can change an output: the
contract's typed and pinned sections and the contents of the code and prompt
files it pins. Any change produces a new hash, and so a new version.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .hashing import sha256_file, sha256_json

Kind = Literal["text", "integer", "number", "boolean", "vector", "matrix", "record", "table", "file", "json"]


class TypeSpec(BaseModel):
    """What a value is and what it means. For vectors, model, instruction and
    post-processing are part of the type: vectors that differ in any of them
    cannot be compared (checks.assert_comparable). A matrix is a stack of
    vectors of one type, kept as a NumPy file in the store and referred to by
    its path and SHA-256."""

    model_config = ConfigDict(extra="forbid")

    kind: Kind
    meaning: str
    range: list[float] | None = None
    values: list[Any] | None = None
    fields: dict[str, str] | None = None
    model: str | None = None
    instruction: str | None = None
    postprocessing: str | None = None
    optional: bool = False


class Typed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inputs: dict[str, TypeSpec]
    outputs: dict[str, TypeSpec]


class Pinned(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: list[str]
    prompts: list[str] = Field(default_factory=list)
    model: dict[str, Any] | None = None
    tools: dict[str, str] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)


class Persisted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Literal["inputs_hash+config_hash"]
    regenerate: Literal["never"]
    # For a deterministic component whose outputs come from a numerical optimizer: the relative
    # difference within which a recomputation still reproduces the stored output (Study B, B1).
    # Absent, the output must be reproduced exactly, up to rounding in the last digits.
    reproduced_within: float | None = None


class Check(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: Literal["unit_tests", "reliability", "agreement", "spot_check", "consistency", "validity", "determinism"]
    metric: str | None = None
    threshold: str | None = None
    result: str | None = None
    evidence: str | None = None


class Validated(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["provisional", "validated"]
    population: str | None = None
    checks: list[Check]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: str
    version: str
    role: Literal["extractor", "representer", "judge", "generator", "validator", "aggregator", "orchestrator"]
    deterministic: bool
    description: str
    typed: Typed
    pinned: Pinned
    persisted: Persisted
    validated: Validated
    card: str


def load_contract(component_dir: Path) -> Contract:
    path = Path(component_dir) / "contract.yaml"
    return Contract.model_validate(yaml.safe_load(path.read_text()))


def resolved_pins(contract: Contract, component_dir: Path) -> dict:
    """The pinned section with each code and prompt file replaced by its hash."""
    component_dir = Path(component_dir)
    pins = contract.pinned.model_dump()
    for key in ("code", "prompts"):
        files = {}
        for rel in pins[key]:
            path = (component_dir / rel).resolve()
            if not path.is_file():
                raise FileNotFoundError(f"{contract.component}: pinned file not found: {rel}")
            files[rel] = sha256_file(path)
        pins[key] = files
    return pins


def config_hash(contract: Contract, component_dir: Path) -> str:
    return sha256_json({
        "component": contract.component,
        "version": contract.version,
        "typed": contract.typed.model_dump(),
        "pinned": resolved_pins(contract, component_dir),
    })
