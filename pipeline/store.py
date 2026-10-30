"""A content-addressed store for component outputs, an index from
(component, configuration hash, inputs hash) to stored outputs, and the
provenance records of every run. Everything lives under data/store/, or the
store of the data folder that COMPAI_DATA names; git ignores the competition's
records, but the public repository tracks the synthetic competition's store.

    objects/<aa>/<sha256>.json                       outputs, named by the hash of their content
    files/<aa>/<sha256>.<suffix>                     large outputs, such as matrices of vectors
    index/<component>/<config hash>/<inputs hash>.json   which output a run produced
    provenance/<component>/<record id>.json          one record per run
"""

import json
import os
import tempfile
from pathlib import Path

from .hashing import canonical_json, sha256_bytes
from .paths import data_dir, store_dir


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


class Store:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else store_dir()

    # Objects
    def put(self, obj) -> str:
        text = canonical_json(obj)
        sha = sha256_bytes(text.encode("utf-8"))
        path = self.root / "objects" / sha[:2] / f"{sha}.json"
        if not path.exists():
            _write_atomic(path, text)
        return sha

    def get(self, sha: str):
        return json.loads((self.root / "objects" / sha[:2] / f"{sha}.json").read_text(encoding="utf-8"))

    # Index
    def _index_path(self, component: str, config_hash: str, inputs_hash: str) -> Path:
        return self.root / "index" / component / config_hash / f"{inputs_hash}.json"

    def lookup(self, component: str, config_hash: str, inputs_hash: str) -> dict | None:
        path = self._index_path(component, config_hash, inputs_hash)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def record_run(self, component: str, config_hash: str, inputs_hash: str, output_sha: str, record_id: str) -> dict:
        """The first run of a configuration on given inputs becomes its stored
        output; later deliberate reruns are listed beside it, never replace it."""
        entry = self.lookup(component, config_hash, inputs_hash)
        if entry is None:
            entry = {"output": output_sha, "record": record_id, "reruns": []}
        else:
            entry["reruns"].append({"output": output_sha, "record": record_id})
        _write_atomic(self._index_path(component, config_hash, inputs_hash), canonical_json(entry))
        return entry

    # Provenance
    def put_record(self, component: str, record: dict) -> Path:
        path = self.root / "provenance" / component / f"{record['id'].split(':')[-1]}.json"
        _write_atomic(path, json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True))
        return path

    def get_record(self, component: str, record_id: str) -> dict:
        path = self.root / "provenance" / component / f"{record_id.split(':')[-1]}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    # Files
    def put_file(self, data: bytes, suffix: str) -> dict:
        """Keep bytes under their hash; returns a file reference whose path is
        relative to the data folder, so that the store can be moved."""
        sha = sha256_bytes(data)
        path = self.root / "files" / sha[:2] / f"{sha}{suffix}"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        return {"path": str(path.relative_to(data_dir())), "sha256": sha}


def resolve(ref: dict) -> Path:
    """The path of a file reference: absolute, or relative to the data folder."""
    path = Path(ref["path"])
    return path if path.is_absolute() else data_dir() / path
