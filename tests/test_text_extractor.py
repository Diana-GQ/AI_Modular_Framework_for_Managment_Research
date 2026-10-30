import pytest

from pipeline.runner import Component
from tests import synthetic

PLAN = "Umbrellas for rainy cities sold by subscription to commuters"
MARKET = "The market is every commuter who walks more than ten minutes a day in a city with over one hundred rainy days a year"


@pytest.fixture
def extractor():
    return Component("text_extractor")


def test_pdf(tmp_path, extractor):
    path = synthetic.pdf(tmp_path / "plan.pdf", [f"{PLAN}. {MARKET}.", MARKET])
    out = extractor.run({"file": synthetic.file_ref(path)}).outputs
    assert out["method"] == "pypdfium2"
    assert out["pages"] == 2
    first, second = out["text"].split("\n\n")
    assert " ".join(first.split()) == f"{PLAN}. {MARKET}." and " ".join(second.split()) == MARKET
    assert out["words"] == len(PLAN.split()) + 2 * len(MARKET.split())
    assert out["needs_ocr"] is False


def test_pdf_with_little_text_is_flagged(tmp_path, extractor):
    path = synthetic.pdf(tmp_path / "short.pdf", [PLAN, ""])
    assert extractor.run({"file": synthetic.file_ref(path)}).outputs["needs_ocr"] is True


def test_pdf_without_text_layer_is_flagged(tmp_path, extractor):
    path = synthetic.pdf(tmp_path / "scan.pdf", ["", ""])
    out = extractor.run({"file": synthetic.file_ref(path)}).outputs
    assert out["words"] == 0 and out["pages"] == 2
    assert out["needs_ocr"] is True


def test_docx_keeps_paragraphs_and_tables_in_order(tmp_path, extractor):
    path = synthetic.docx(tmp_path / "plan.docx", [PLAN, "Pricing follows."],
                          table=[["Year", "Revenue"], ["1", "100"]])
    out = extractor.run({"file": synthetic.file_ref(path)}).outputs
    assert out["method"] == "python-docx"
    assert out["pages"] is None
    assert out["text"].splitlines() == [PLAN, "Pricing follows.", "Year | Revenue", "1 | 100"]
    assert out["needs_ocr"] is False


def test_docx_headers_footers_and_merged_cells(tmp_path, extractor):
    from docx import Document

    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Team header"
    doc.sections[0].footer.paragraphs[0].text = "Page footer"
    doc.add_paragraph(PLAN)
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).merge(table.cell(0, 1)).text = "Financials"
    table.cell(1, 0).text, table.cell(1, 1).text = "Year 1", "100"
    doc.save(tmp_path / "plan.docx")
    out = extractor.run({"file": synthetic.file_ref(tmp_path / "plan.docx")}).outputs
    assert out["text"].splitlines() == ["Team header", PLAN, "Financials", "Year 1 | 100", "Page footer"]


def test_ligatures_become_letters():
    from pipeline.runner import _load_module
    from pipeline.paths import COMPONENTS

    module = _load_module(COMPONENTS / "text_extractor")
    assert module.normalize("\ufb01nance and pro\ufb01t") == "finance and profit"


def test_doc(tmp_path, extractor):
    path = synthetic.doc(tmp_path / "plan.doc", PLAN)
    if path is None:
        pytest.skip("textutil is available only on macOS")
    out = extractor.run({"file": synthetic.file_ref(path)}).outputs
    assert out["method"] == "textutil"
    assert out["text"] == PLAN


def test_same_content_under_another_name_is_not_extracted_again(tmp_path, extractor):
    first = synthetic.pdf(tmp_path / "a.pdf", [PLAN])
    second = tmp_path / "b.pdf"
    second.write_bytes(first.read_bytes())
    assert extractor.run({"file": synthetic.file_ref(first)}).cached is False
    assert extractor.run({"file": synthetic.file_ref(second)}).cached is True


def test_unsupported_type(tmp_path, extractor):
    path = tmp_path / "plan.txt"
    path.write_text(PLAN)
    with pytest.raises(ValueError):
        extractor.run({"file": synthetic.file_ref(path)})
