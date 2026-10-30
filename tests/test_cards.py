import shutil

from pipeline.cards import BEGIN, END, render
from pipeline.paths import COMPONENTS


def test_render_fills_the_generated_section_and_is_idempotent(tmp_path):
    comp = tmp_path / "weighted_score"
    shutil.copytree(COMPONENTS / "weighted_score", comp)
    render(comp)
    first = (comp / "card.md").read_text()
    render(comp)
    assert (comp / "card.md").read_text() == first
    section = first.split(BEGIN, 1)[1].split(END, 1)[0]
    assert "Configuration hash" in section and "Formula unit tests" in section
