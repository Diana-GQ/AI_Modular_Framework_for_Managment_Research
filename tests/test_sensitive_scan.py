"""The sensitive-term check's word test finds the same matches as running every pattern on every line."""

import contextlib
import io
import re
import sys
from re import _casefix

import _sre

from pipeline.paths import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import check_sensitive  # noqa: E402


def every_pattern(text, patterns, allow):
    """The scan without the word test: every pattern on every line."""
    found = []
    for n, line in enumerate(text.splitlines(), start=1):
        for rx in allow:
            line = rx.sub(lambda m: " " * len(m.group(0)), line)
        found += [(n, category, m.group(0)) for category, _, rx in patterns for m in rx.finditer(line)]
    return found


def scanned(text, patterns, allow):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        check_sensitive.scan("t", text, patterns, allow, True)
    found = []
    for line in out.getvalue().splitlines():
        where, category, match = line.split(": ", 2)
        found.append((int(where.split(":")[1]), category, match))
    return found


def test_word_keys_follow_case_insensitive_matching():
    # Characters that the regular expressions match case-insensitively form classes: those with the same
    # lower case, joined by the extra cases. Every class must give one key, and only the combining iota may
    # join a letter to a character that is not one.
    chars = "".join(chr(i) for i in range(0x110000) if not 0xD800 <= i <= 0xDFFF)
    classes = {}
    for c in chars:
        classes.setdefault(_sre.unicode_tolower(ord(c)), set()).add(c)
    for low, extras in _casefix._EXTRA_CASES.items():
        for e in extras:
            classes.setdefault(low, set()).update(classes.get(e, set()))
    for members in classes.values():
        if check_sensitive.LETTER_MARK in members:
            continue
        assert len({bool(check_sensitive.WORD.fullmatch(c)) for c in members}) == 1, members
        words = [c for c in members if check_sensitive.WORD.fullmatch(c)]
        assert len({check_sensitive.word_key(c) for c in words}) <= 1, members
    as_ascii = {m.group(0) for a in "abcdefghijklmnopqrstuvwxyz" for m in re.finditer(a, chars, re.I)
                if not m.group(0).isascii()}
    assert as_ascii == set(check_sensitive.AS_ASCII)


def test_scan_finds_what_every_pattern_finds(tmp_path):
    terms = tmp_path / "terms.tsv"
    terms.write_text("\n".join([
        "person\tAda Quill", "venture\tPascal Works", "file_name\tKelvo", "institution\tIstan",
        "person\tJosé Ortiz", "venture\tιωτα", "file_name\tO'Brien", "institution\tAB",
    ]) + "\n")
    allow_list = tmp_path / "allow.txt"
    allow_list.write_text("AB testing\n")
    patterns, allow = check_sensitive.load_patterns(terms, allow_list)
    texts = [
        "Ada  Quill met ADA QUILL; ada quillon is not her.\nPascal Works and Paſcal Works.",
        "Kelvo, kelvo_x and xkelvo. İstan, ıstan and Istanbul.",
        "JOSÉ ORTIZ, José Ortiz and Jose Ortiz. O'Brien and O'BRIEN.",
        "ͅωτα and ΙΩΤΑ.\nAB testing, an AB test, ab@x.",
        "Ada\nQuill across lines is not a match.",
    ]
    for text in texts:
        expected = every_pattern(text, patterns, allow)
        assert scanned(text, patterns, allow) == expected
    assert len(every_pattern(texts[1], patterns, allow)) == 4
    assert len(every_pattern(texts[3], patterns, allow)) == 3
