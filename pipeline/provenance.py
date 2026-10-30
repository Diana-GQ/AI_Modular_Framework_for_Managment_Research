"""Provenance records in the terms of W3C PROV: each run of a component is an
activity that used input entities and generated an output entity, associated
with the person who ran it and the software environment."""

import functools
import importlib.metadata
import os
import platform
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from .paths import ROOT

PACKAGES = ("anthropic", "modal", "pandas", "pyarrow", "pydantic", "pypdfium2", "python-docx", "openpyxl", "pyyaml")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@functools.lru_cache(maxsize=1)
def environment() -> dict:
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        changes = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip()
    except OSError:
        commit, changes = "", ""
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions,
        "repository_commit": commit or None,
        # Uncommitted or untracked files: the commit alone does not identify the code.
        # Components' own code is identified anyway, by the hashes in the configuration hash.
        "repository_has_uncommitted_changes": bool(changes),
    }


@functools.lru_cache(maxsize=1)
def agent() -> str:
    try:
        name = subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        name = ""
    return name or os.environ.get("USER", "unknown")


def make_record(*, contract, config_hash: str, inputs_hash: str, input_hashes: dict, output_sha: str,
                started: str, ended: str, batch_id: str | None = None, rerun: bool = False,
                details: dict | None = None) -> dict:
    return {
        "id": f"urn:uuid:{uuid.uuid4()}",
        "type": "prov:Activity",
        "prov:startedAtTime": started,
        "prov:endedAtTime": ended,
        "prov:wasAssociatedWith": {"agent": agent(), "software": environment()},
        "prov:used": [{"role": name, "entity": f"sha256:{sha}"} for name, sha in sorted(input_hashes.items())],
        "prov:generated": [{"role": "output", "entity": f"sha256:{output_sha}"}],
        "component": {
            "name": contract.component,
            "version": contract.version,
            "config_hash": config_hash,
            "model": contract.pinned.model,
            "deterministic": contract.deterministic,
        },
        "inputs_hash": inputs_hash,
        "batch_id": batch_id,
        "rerun": rerun,
        "details": details or {},
    }
