"""The frozen pipeline (task 5.6): every component's version and
configuration hash, recorded in components/frozen.json when the authors froze
the pipeline. The later editions run with these components, so that their
results can be compared with 2019's (design, B5).

    uv run python -m pipeline.freeze check     # which components differ from the frozen list
    uv run python -m pipeline.freeze record    # record the current versions, with the authors' approval

A test fails while any component differs from the list. Changing a frozen
component therefore takes a deliberate step: a new version, recorded on its
card, and the list recorded again.
"""

import json
import sys
from datetime import date

from .contracts import config_hash, load_contract
from .paths import COMPONENTS

FROZEN = COMPONENTS / "frozen.json"


def current() -> dict[str, dict]:
    out = {}
    for d in sorted(p for p in COMPONENTS.iterdir() if (p / "contract.yaml").exists()):
        c = load_contract(d)
        out[d.name] = {"version": c.version, "config_hash": config_hash(c, d)}
    return out


def differences() -> list[str]:
    frozen = json.loads(FROZEN.read_text())["components"]
    now = current()
    found = [f"{name}: not in the frozen list" for name in sorted(now.keys() - frozen.keys())]
    found += [f"{name}: frozen, but no longer present" for name in sorted(frozen.keys() - now.keys())]
    for name in sorted(now.keys() & frozen.keys()):
        if now[name] != frozen[name]:
            found.append(f"{name}: version {frozen[name]['version']} frozen, {now[name]['version']} now; configuration changed"
                         if now[name]["config_hash"] != frozen[name]["config_hash"] else f"{name}: version changed")
    return found


def record() -> None:
    FROZEN.write_text(json.dumps({"frozen": date.today().isoformat(), "components": current()}, indent=1) + "\n")
    print(f"recorded {len(current())} components in {FROZEN.relative_to(COMPONENTS.parent)}")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    if command == "record":
        record()
    elif command == "check":
        found = differences()
        print("\n".join(found) if found else "every component matches the frozen list")
        sys.exit(1 if found else 0)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
