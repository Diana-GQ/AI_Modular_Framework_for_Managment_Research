"""Cards: the human-readable documentation of a component.

The component's owner writes card.md. Between the markers below, this module
writes what the contract records (settings, configuration hash, validation
evidence), so the card cannot drift from the contract:

    <!-- BEGIN GENERATED FROM CONTRACT -->
    <!-- END GENERATED FROM CONTRACT -->

    uv run python -m pipeline.cards components/<name>
"""

import json
import sys
from pathlib import Path

from .contracts import config_hash, load_contract

BEGIN = "<!-- BEGIN GENERATED FROM CONTRACT -->"
END = "<!-- END GENERATED FROM CONTRACT -->"


def generated_section(component_dir: Path) -> str:
    c = load_contract(component_dir)
    lines = [
        f"- **Component:** `{c.component}`, version {c.version}, role {c.role}, "
        f"{'deterministic' if c.deterministic else 'stochastic'}.",
        f"- **Configuration hash:** `{config_hash(c, component_dir)}`",
        f"- **Validation status:** {c.validated.status}" + (f"; population: {c.validated.population}" if c.validated.population else ""),
    ]
    if c.pinned.model:
        lines.append(f"- **Model:** `{json.dumps(c.pinned.model, sort_keys=True)}`")
    if c.pinned.tools:
        lines.append("- **Tools:** " + ", ".join(f"{k} {v}" for k, v in sorted(c.pinned.tools.items())))
    if c.pinned.settings:
        lines.append(f"- **Settings:** `{json.dumps(c.pinned.settings, sort_keys=True)}`")
    lines.append("- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently")
    if c.persisted.reproduced_within:
        lines.append(f"- **Reproduced within:** a relative difference of {c.persisted.reproduced_within:g}; the outputs come from a numerical optimizer")
    lines += ["", "| Check | Kind | Metric | Threshold | Result | Evidence |", "|---|---|---|---|---|---|"]
    for check in c.validated.checks:
        lines.append(f"| {check.name} | {check.kind} | {check.metric or ''} | {check.threshold or ''} | "
                     f"{check.result or 'not yet run'} | {check.evidence or ''} |")
    return "\n".join(lines)


def render(component_dir: Path) -> None:
    component_dir = Path(component_dir)
    card = component_dir / "card.md"
    text = card.read_text()
    if BEGIN not in text or END not in text:
        raise ValueError(f"{card}: missing the generated-section markers")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    card.write_text(f"{head}{BEGIN}\n{generated_section(component_dir)}\n{END}{tail}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        render(Path(arg))
