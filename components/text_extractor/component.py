"""Converts an executive summary (PDF, Word .docx or Word .doc) to plain text,
with its page and word counts. Files whose text layer is nearly empty are
flagged for optical character recognition rather than passed on silently."""

import re
import subprocess
import unicodedata
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MC_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"


def normalize(text: str) -> str:
    """NFKC turns typographic ligatures (such as 'fi' drawn as one glyph) back into letters."""
    text = unicodedata.normalize("NFKC", text).replace("\x00", "")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def from_pdf(path: Path) -> tuple[str, int]:
    """The text that lies within each page's visible area, through PDFium."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    try:
        return "\n\n".join(pdf[i].get_textpage().get_text_bounded() for i in range(len(pdf))), len(pdf)
    finally:
        pdf.close()


def _ooxml_text(root) -> str:
    """Every text node under root, in document order: paragraphs on their own
    lines, cells of a table row joined by ' | '. Text in tables, text boxes and
    tracked insertions is included; tracked deletions are not text nodes, and
    the duplicate fallback copies of text boxes are skipped."""
    parts, last_p, last_cell = [], None, None
    for node in root.iter(W + "t", W + "tab", W + "br", W + "cr"):
        ancestors = list(node.iterancestors())
        if any(a.tag == MC_FALLBACK for a in ancestors):
            continue
        p = next((a for a in ancestors if a.tag == W + "p"), None)
        cell = next((a for a in ancestors if a.tag == W + "tc"), None)
        if p is not last_p and last_p is not None:
            same_row = cell is not None and last_cell is not None and cell is not last_cell \
                and cell.getparent() is last_cell.getparent()
            parts.append(" | " if same_row else "\n")
        last_p, last_cell = p, cell
        parts.append(node.text or "" if node.tag == W + "t" else "\t" if node.tag == W + "tab" else "\n")
    return "".join(parts)


def from_docx(path: Path) -> str:
    """Headers, the body, then footers; a header or footer shared by several sections appears once."""
    from docx import Document

    doc = Document(path)
    headers, footers, seen = [], [], set()
    for section in doc.sections:
        for kind, out in (("header", headers), ("footer", footers)):
            for variant in (kind, f"first_page_{kind}", f"even_page_{kind}"):
                part = getattr(section, variant)
                if part.is_linked_to_previous or id(part.part) in seen:
                    continue
                seen.add(id(part.part))
                out.append(_ooxml_text(part._element))
    return "\n".join(t for t in [*headers, _ooxml_text(doc.element.body), *footers] if t.strip())


def from_doc(path: Path) -> str:
    """Old binary Word files, through macOS's textutil."""
    result = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)], capture_output=True, check=True)
    return result.stdout.decode("utf-8")


def run(inputs: dict, settings: dict) -> dict:
    path = Path(inputs["file"]["path"])
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw, pages = from_pdf(path)
        method = "pypdfium2"
    elif suffix == ".docx":
        raw, pages, method = from_docx(path), None, "python-docx"
    elif suffix == ".doc":
        raw, pages, method = from_doc(path), None, "textutil"
    else:
        raise ValueError(f"unsupported file type: {suffix}")
    text = normalize(raw)
    words = len(text.split())
    needs_ocr = suffix == ".pdf" and words < settings["min_words_per_page"] * max(pages, 1)
    return {"text": text, "pages": pages, "words": words, "method": method, "needs_ocr": needs_ocr}
