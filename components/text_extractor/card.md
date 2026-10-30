# Card: text extractor

**Purpose.** Converts each executive summary to plain text for the AI judges and the text measures, and counts its pages and words.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses pypdfium2 and PDFium (Apache-2.0 or BSD-3-Clause), python-docx (MIT) and macOS's textutil.

**Data terms.** Runs on project machines; sends nothing to any service.

**How it reads each format.**
- *PDF*: PDFium's text of each page's visible area, pages separated by a blank line.
- *Word .docx*: every text node in document order, including tables, text boxes and tracked insertions; headers first and footers last, once each.
- *Word .doc*: macOS's `textutil`.
- All text is put in Unicode normal form NFKC, which turns typographic ligatures (such as "fi" drawn as one glyph) back into letters.

**Choice of PDF tool.** On the 149 PDFs of 2019, four tools were compared with the authors' earlier extraction of the same files (word overlap, word order, and words run together). PyMuPDF and PDFium were best and nearly equal; pypdf ran words together on several files. PDFium was chosen because its licence is permissive, while PyMuPDF's is the AGPL.

**Agreement with the authors' earlier extraction (2019).** The median agreement is 0.996 over the 160 summaries the earlier extraction covers (it skipped the one `.doc` file). The nine summaries below 0.95:
- three Word files, where this extractor also reads tables and headers, which the earlier extraction missed (in one file it found no text at all);
- six PDFs where the tools differ on layout: word order in multi-column pages, text the file draws twice, and a nine-page slide-style file with about 26 words a page.

All nine are in the authors' visual check. The earlier extraction's page counts differ from the files' for ten PDFs whose texts agree; page counts here come from PDFium and match pypdf's on all 149 PDFs.

**The authors' visual check (2019).** Of 20 extractions, every one was complete, and 4 had their reading order wrong: a slide deck read in the wrong direction, a page mixing one and two columns, a two-column layout with images, and a file whose second page came first. All 4 were among the summaries that agreed least with the earlier extraction, so the comparison flags such files in advance. In the file with reversed pages, a damaged font also turned the letters "ti" into an odd character.

**Known failure modes.**
- Layout-heavy PDFs can come out with words in an unusual order, or with text the file draws twice.
- Text inside images (charts, logos, screenshots) is not extracted, although human judges could read it.
- Scanned PDFs have no text layer; they are flagged (`needs_ocr`) for optical character recognition, which is not built yet because no 2019 file needs it.
- Old `.doc` files are read with macOS's `textutil`, so re-extracting them needs a Mac; their stored text can be reused anywhere.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `text_extractor`, version 1.0.0, role extractor, deterministic.
- **Configuration hash:** `8d2481017c07f326d41612c2ed6ab30978d19a88c08e9dd5e60e0ee0abe9827e`
- **Validation status:** validated; population: The 2019 competition's executive summaries (PDF, .docx and one .doc)
- **Tools:** pdfium 156.0.8076.0 (bundled with pypdfium2), pypdfium2 5.14.0, python-docx 1.2.0, textutil macOS 15.7.9 (used only for .doc files)
- **Settings:** `{"min_words_per_page": 20}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic files | unit_tests |  | all pass | pass | tests/test_text_extractor.py |
| Agreement with the authors' earlier extraction of the same files | agreement | for each summary, the smaller of the two shares of each extraction's words found in the other | median at least 0.95; every summary below 0.95 explained | pass: median 0.996 over 160 summaries; the 9 below 0.95 are explained on the card | data/reports/2019_extraction_check.json (pipeline/stages/extract.py) |
| Visual check of 20 extractions against their files | spot_check |  | no material omissions | pass: 20 of 20 complete; reading order wrong in 4, all among the summaries the comparison had flagged (a slide deck, mixed or two-column layouts with images, pages in reverse order); figures inside images are not extracted | data/reports/2019_spot_check/results.csv, filled in by the authors |
<!-- END GENERATED FROM CONTRACT -->
