"""Plan Phase 6: Study B, the replicability audit (design, Section 5).

    uv run python -m pipeline.stages.study_b reproduce 2019        # B1 on a year's records
    uv run python -m pipeline.stages.study_b reproduce synthetic   # B1 on the synthetic competition

B1 rebuilds the analysis in a fresh copy of the package: the repository's
files, a new environment built from the lock file, the year's sources, the
private key and term list, the records of the judges' runs, and the stored
outputs of the components that call a model (the AI judges and the
embedders). Every other component is computed again from these, and each of
its outputs is compared with the output stored in the original; so are the
tables and the reports. Models cannot be called in the copy: a missing AI
output stops the run instead of being generated again. The copy stays inside
the data folder and is deleted afterwards.
"""

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..paths import COMPONENTS, ROOT, data_dir
from ..runner import Component

# The records of the original runs that later stages read: which configuration
# each judge ran under, the pilot's entries, the GPU sessions, the embedders' re-execution.
RUN_RECORDS = ("{year}_pilot_configs.json", "{year}_full_configs.json", "{year}_pilot_entries.json",
               "{year}_qwen_sessions.json", "{year}_embedding_reexecution.json")
STAGES = (("tests", "pytest -q"),
          *((name, f"python -m pipeline.stages.{module} {args}") for name, module, args in (
              ("pseudonymize", "pseudonymize", "{year}"), ("extract", "extract", "{year}"), ("tables", "tables", "{year}"),
              ("profile", "profile", "{year}"), ("pilot report", "judge", "report {year}"),
              ("full-run report", "judge", "full-report {year}"), ("study A", "study_a", "report {year}"))))
# Identifiers of this run's provenance records and outputs, which a new run replaces.
RUN_IDS = re.compile(r"`[0-9a-f]{8}…`|`[0-9a-f]{12}`")
TABLES = ("entries", "documents", "evaluations", "judges", "evaluations_ai")
# The synthetic competition's outputs that the public repository carries in git.
PUBLISHED_OUTPUTS = ("synthetic/data/store/", "synthetic/data/tables/")
REPORTS = ("{year}_extraction_check.json", "{year}_sensitive_check.json", "{year}_profile.json", "{year}_pilot.json",
           "{year}_full_run.json", "{year}_study_a_report.md")


def model_components() -> list[str]:
    """The components that call a model, except the synthetic competition's generators: their stored
    outputs are part of the package. The generators' outputs are not needed, nor published: the synthetic
    competition's files are what they wrote."""
    names = sorted(d.name for d in COMPONENTS.iterdir() if (d / "contract.yaml").exists())
    return [n for n in names if Component(n).contract.pinned.model and not n.startswith("synthetic_")]


def file_refs(obj) -> list[str]:
    """Paths of the stored files an output refers to, such as matrices of vectors."""
    if isinstance(obj, dict):
        if isinstance(obj.get("path"), str) and obj["path"].startswith("store/files/"):
            return [obj["path"]]
        return [p for v in obj.values() for p in file_refs(v)]
    if isinstance(obj, list):
        return [p for v in obj for p in file_refs(v)]
    return []


def carry_store(source: Path, target: Path, components: list[str]) -> int:
    """Copy the given components' stored outputs, index entries, provenance
    records and files from one data folder's store to another's."""
    copied = 0
    for name in components:
        index = source / "store" / "index" / name
        if not index.exists():
            continue
        for path in index.rglob("*.json"):
            entry = json.loads(path.read_text())
            for sha in [entry["output"], *(r["output"] for r in entry["reruns"])]:
                obj = source / "store" / "objects" / sha[:2] / f"{sha}.json"
                (target / obj.relative_to(source)).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(obj, target / obj.relative_to(source))
                for ref in file_refs(json.loads(obj.read_text())):
                    (target / ref).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source / ref, target / ref)
            (target / path.relative_to(source)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target / path.relative_to(source))
            copied += 1
        shutil.copytree(source / "store" / "provenance" / name, target / "store" / "provenance" / name, dirs_exist_ok=True)
    return copied


def package_files() -> list[str]:
    """The repository's files, as git would publish them: tracked, or new and not ignored. The synthetic
    competition's stored outputs and tables are left out, though the public repository tracks them: they
    are what the copy computes again, and a stored output would be reused instead."""
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, check=True).stdout.decode()
    return [p for p in out.split("\0") if p and (ROOT / p).is_file() and not p.startswith(PUBLISHED_OUTPUTS)]


def numerically_equal(a, b, rel: float = 1e-9) -> bool:
    """The same structure, text and integers, and numbers equal to within rounding."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(numerically_equal(a[k], b[k], rel) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(numerically_equal(x, y, rel) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return False
        return (math.isnan(a) and math.isnan(b)) or math.isclose(a, b, rel_tol=rel, abs_tol=1e-12)
    return a == b


def compare_store(original: Path, fresh: Path, carried: list[str]) -> dict:
    """Each output computed in the copy against the original's stored output for
    the same component, configuration and inputs: identical, bit for bit; equal
    to within rounding (numbers within a relative 1e-9); within the tolerance the
    component's contract declares, for outputs that come from an optimizer; or different."""
    out = {}
    load = lambda root, sha: json.loads((root / "store" / "objects" / sha[:2] / f"{sha}.json").read_text())
    for component in sorted(p.name for p in (fresh / "store" / "index").iterdir()):
        if component in carried:
            continue
        declared = Component(component).contract.persisted.reproduced_within if (COMPONENTS / component).is_dir() else None
        counts = {"identical": 0, "equal_within_rounding": 0, "within_declared_tolerance": 0, "different": 0, "not_in_original": 0}
        for path in (fresh / "store" / "index" / component).rglob("*.json"):
            twin = original / path.relative_to(fresh)
            if not twin.exists():
                counts["not_in_original"] += 1
                continue
            a, b = json.loads(twin.read_text())["output"], json.loads(path.read_text())["output"]
            if a == b:
                counts["identical"] += 1
            elif numerically_equal(x := load(original, a), y := load(fresh, b)):
                counts["equal_within_rounding"] += 1
            elif declared and numerically_equal(x, y, rel=declared):
                counts["within_declared_tolerance"] += 1
            else:
                counts["different"] += 1
        out[component] = counts
    return out


def compare_outputs(original: Path, fresh: Path, year: int) -> dict:
    tables, reports = {}, {}
    for name in TABLES:
        a, b = original / "tables" / str(year) / f"{name}.parquet", fresh / "tables" / str(year) / f"{name}.parquet"
        if not b.exists():
            tables[name] = "missing"
            continue
        if not a.exists():
            # The original was not published, so there is nothing to compare with.
            tables[name] = "not in original"
            continue
        x, y = pd.read_parquet(a), pd.read_parquet(b)
        try:
            pd.testing.assert_frame_equal(x, y, rtol=1e-9)
            tables[name] = "identical" if x.equals(y) else "equal within rounding"
        except AssertionError:
            tables[name] = "different"
    for pattern in REPORTS:
        name = pattern.format(year=year)
        a, b = original / "reports" / name, fresh / "reports" / name
        if not b.exists():
            reports[name] = "missing"
        elif not a.exists():
            reports[name] = "not in original"
        elif name.endswith(".md"):
            # A report gives the day it was written and the identifiers of this run's records and outputs;
            # the configurations behind them are compared in the store.
            strip = lambda p: [RUN_IDS.sub("`id`", l) for l in p.read_text().splitlines() if not l.startswith("Written ")]
            reports[name] = "identical" if strip(a) == strip(b) else "different"
        else:
            x, y = json.loads(a.read_text()), json.loads(b.read_text())
            reports[name] = "identical" if x == y else "equal within rounding" if numerically_equal(x, y) else "different"
    return {"tables": tables, "reports": reports}


def reproduce(which: str, keep: bool = False) -> None:
    synthetic = which == "synthetic"
    year = 2000 if synthetic else int(which)
    original = (ROOT / "synthetic" / "data") if synthetic else data_dir()
    workspace = original / "reproduction" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    package = workspace / "package"
    fresh = package / ("synthetic/data" if synthetic else "data")
    timings, started = {}, time.time()

    files = package_files()
    for p in files:
        (package / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / p, package / p)
    if synthetic:
        # The package carries the synthetic competition's earlier results; they are what is reproduced.
        shutil.rmtree(fresh / "reports", ignore_errors=True)
    else:
        shutil.copytree(original / "raw" / str(year), fresh / "raw" / str(year))
        (fresh / "manifests").mkdir(parents=True, exist_ok=True)
        shutil.copy2(original / "manifests" / f"{year}_documents.csv", fresh / "manifests")
        for name in ("code_key.csv", "sensitive_terms.tsv", "sensitive_allow.txt"):
            (fresh / "private").mkdir(parents=True, exist_ok=True)
            shutil.copy2(original / "private" / name, fresh / "private" / name)
    (fresh / "reports").mkdir(parents=True, exist_ok=True)
    for pattern in RUN_RECORDS:
        if (original / "reports" / pattern.format(year=year)).exists():
            shutil.copy2(original / "reports" / pattern.format(year=year), fresh / "reports")
    carried = model_components()
    carried_entries = carry_store(original, fresh, carried)
    timings["copy"] = round(time.time() - started, 1)

    env = {k: v for k, v in os.environ.items() if not k.startswith(("VIRTUAL_ENV", "UV_", "COMPAI_"))}
    # No model can be called from the copy: the API key is missing and Modal's credentials are invalid.
    env |= {"ANTHROPIC_API_KEY": "", "MODAL_TOKEN_ID": "blocked", "MODAL_TOKEN_SECRET": "blocked",
            "COMPAI_DATA": str(fresh)}
    log = open(original / "reports" / f"{year}_b1_reproduction.log", "w")
    t = time.time()
    subprocess.run(["uv", "sync", "--frozen"], cwd=package, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    timings["environment"] = round(time.time() - t, 1)
    failed = None
    for name, command in STAGES:
        t = time.time()
        command = command.format(year=year)
        print(f"running: {command}", flush=True)
        log.write(f"\n$ {command}\n")
        log.flush()
        done = subprocess.run(["uv", "run", "--frozen", *command.split()], cwd=package, env=env, stdout=log,
                              stderr=subprocess.STDOUT)
        timings[name] = round(time.time() - t, 1)
        if done.returncode:
            failed = command
            break
    log.close()
    timings["total"] = round(time.time() - started, 1)

    store = compare_store(original, fresh, carried)
    totals = {k: sum(c[k] for c in store.values())
              for k in ("identical", "equal_within_rounding", "within_declared_tolerance", "different", "not_in_original")}
    report = {
        "check": "B1: the analysis rebuilt in a fresh copy of the package, from the stored outputs of the components that call a model",
        "data": "the synthetic competition" if synthetic else f"the {year} records", "year": year,
        "date": datetime.now(timezone.utc).date().isoformat(), "failed_stage": failed,
        "carried_components": carried, "carried_index_entries": carried_entries,
        "recomputed_outputs": totals, "share_identical": round(totals["identical"] / max(1, sum(totals.values())), 4),
        "share_reproduced": round((totals["identical"] + totals["equal_within_rounding"] + totals["within_declared_tolerance"])
                                  / max(1, sum(totals.values())), 4),
        "by_component": store, **compare_outputs(original, fresh, year), "seconds": timings,
        "environment": "a new copy of the repository's files and a new environment from uv.lock, on the authors' computer",
    }
    (original / "reports" / f"{year}_b1_reproduction.json").write_text(json.dumps(report, indent=1) + "\n")
    if not keep:
        shutil.rmtree(workspace)
        if not any((original / "reproduction").iterdir()):
            (original / "reproduction").rmdir()
    print(json.dumps({k: report[k] for k in ("failed_stage", "recomputed_outputs", "share_identical", "share_reproduced", "tables",
                                             "reports", "seconds")}, indent=1))


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] != "reproduce":
        sys.exit(__doc__)
    reproduce(sys.argv[2], keep="--keep" in sys.argv)


if __name__ == "__main__":
    main()
