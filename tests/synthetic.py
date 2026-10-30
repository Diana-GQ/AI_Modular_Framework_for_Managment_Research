"""Synthetic files for tests. They contain invented text only, never project data."""

import shutil
import subprocess
from pathlib import Path

from pipeline.hashing import sha256_file


def _lines(text: str, width: int = 80) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def pdf(path: Path, pages: list[str]) -> Path:
    """A PDF with Helvetica text, one string per page, wrapped to fit the page;
    an empty string gives a page with no text layer."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica")}))
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        if text:
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
            stream = DecodedStreamObject()
            body = " T* ".join(f"({line}) Tj" for line in _lines(text))
            stream.set_data(f"BT /F1 11 Tf 14 TL 72 720 Td {body} ET".encode("latin-1"))
            page[NameObject("/Contents")] = writer._add_object(stream)
    with open(path, "wb") as f:
        writer.write(f)
    return path


def docx(path: Path, paragraphs: list[str], table: list[list[str]] | None = None) -> Path:
    from docx import Document

    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    if table:
        t = doc.add_table(rows=len(table), cols=len(table[0]))
        for i, row in enumerate(table):
            for j, cell in enumerate(row):
                t.cell(i, j).text = cell
    doc.save(path)
    return path


def doc(path: Path, text: str) -> Path | None:
    """An old binary Word file, made with macOS's textutil; None where textutil is missing."""
    if not shutil.which("textutil"):
        return None
    source = path.with_suffix(".txt")
    source.write_text(text)
    subprocess.run(["textutil", "-convert", "doc", str(source), "-output", str(path)], check=True)
    return path


def file_ref(path: Path) -> dict:
    return {"path": str(path), "sha256": sha256_file(path)}


def workbook(path: Path, settings: dict, applications: list[dict], judging: list[dict]) -> Path:
    """An export workbook laid out as the records tables' settings describe,
    with invented headers made of the expected fragments."""
    from openpyxl import Workbook

    wb = Workbook()
    wb.remove(wb.active)
    for part, rows in (("applications", applications), ("judging", judging)):
        spec = settings[part]
        ws = wb.create_sheet(spec["sheet"])
        width = max(c["column"] for c in spec["columns"].values()) + 2
        header = [f"Unused column {i}" for i in range(width)]
        for name, col in spec["columns"].items():
            header[col["column"]] = " - ".join(col["header"])
        ws.append(header)
        for row in rows:
            values = ["filler"] * width
            for name, col in spec["columns"].items():
                values[col["column"]] = row.get(name)
            ws.append(values)
    wb.save(path)
    return path
