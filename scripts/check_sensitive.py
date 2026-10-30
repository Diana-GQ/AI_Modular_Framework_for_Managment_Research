"""Keep personal data and the names of institutions tied to the data out of git.

The term list is built from the competition exports in data/raw/ and kept in
data/private/, which git ignores, so the list itself is never committed.

  uv run --with openpyxl python scripts/check_sensitive.py build
  uv run python scripts/check_sensitive.py check             # files git would commit
  uv run python scripts/check_sensitive.py check --staged    # staged files (pre-commit hook)
  uv run python scripts/check_sensitive.py check --message FILE   # commit message
  uv run python scripts/check_sensitive.py check --history   # every commit so far
  uv run python scripts/check_sensitive.py install-hooks

Matches are reported by file, line and category, with the matched text masked.
Add --show to print it; leave it off where the output is logged or shared.
False positives go in data/private/sensitive_allow.txt, one phrase per line:
a term inside an allowed phrase (e.g., a publisher's full name) is ignored,
while the same term elsewhere is still reported. The allow list stays private
because it would reveal which terms are in the data. Single-word names that
are ordinary English words are not listed, so the check does not replace
reading what you commit.
"""

import argparse
import functools
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "data" / "private"
TERMS = PRIVATE / "sensitive_terms.tsv"
ALLOW = PRIVATE / "sensitive_allow.txt"

HYPERLINK = re.compile(r'HYPERLINK\("([^"]+)"\s*,\s*"([^"]*)"\)')
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Domains reserved for examples (RFC 2606), as in the synthetic competition: never a real address.
EXAMPLE_EMAIL = re.compile(r"@(?:[\w-]+\.)*example\.(?:com|org|net)$", re.I)
URL_HOST = re.compile(r"(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)", re.I)

# Words that are never identifying on their own. A phrase is listed only if it
# has at least one word outside this set.
GENERIC = set("""
a an and the of for in at on to by with de la le
exec executive summary summaries business plan plans final draft copy version
pdf doc docx ppt pptx xlsx jpg png page one two pager document paper concept
team company inc llc corp co ltd group venture ventures competition contest
new round submission application entry status tax cap table live logo
slides deck pitch presentation proof transcript verification form
university college school institute state polytechnic tech technology
technologies community academy center centre
""".split())
MAIL_PROVIDERS = set("""
gmail googlemail yahoo ymail hotmail outlook live msn icloud me mac aol
protonmail proton pm gmx mail comcast att verizon sbcglobal qq
""".split())
COMMON_SITES = set("""
google youtube youtu facebook fb instagram linkedin twitter x tiktok medium
github wix wixsite squarespace wordpress weebly godaddy godaddysites shopify
myshopify webs webflow jimdo strikingly carrd yola yolasite site123 blogspot
tumblr bit ly
irs gov amazon apple microsoft dropbox box
""".split())


def dictionary_words():
    path = Path("/usr/share/dict/words")
    if not path.exists():
        return set()
    return {w.strip().lower() for w in path.read_text(errors="ignore").split()}


def camel_split(token):
    token = re.sub(r"(University|Institute|College|School)(of|at|in)(?=[A-Z])", r"\1 \2 ", token)
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", token)


def words_of(text):
    return re.findall(r"[A-Za-z][A-Za-z'&]*", text)


def distinctive(text, dictionary):
    """True if the text has a word that is neither generic nor, when the text
    is a single word, an ordinary English word."""
    words = [w.lower() for w in words_of(text)]
    specific = [w for w in words if w not in GENERIC]
    if not specific:
        return False
    if len(words) == 1:
        word = words_of(text)[0]
        long_enough = len(word) >= 4 or (len(word) == 3 and word.isupper())
        return long_enough and words[0] not in dictionary
    return True


def domain_label(host):
    parts = host.lower().split(".")
    if len(parts) < 2:
        return None
    label = parts[-2]
    if parts[-1] in {"uk", "au", "nz", "br", "mx", "in", "jp"} and len(parts) >= 3:
        label = parts[-3]
    return label


def build():
    import openpyxl

    dictionary = dictionary_words()
    terms = set()
    entries = Counter()

    def add(category, text):
        text = " ".join(str(text).split())
        if text:
            terms.add((category, text))

    def add_name_field(category, text):
        """A file-name field, venture or institution name, as written and with
        CamelCase split into words."""
        text = re.sub(r"\.(pdf|docx?|pptx?|xlsx|jpe?g|png)$", "", text, flags=re.I)
        text = re.sub(r"[\d.()\[\]]+", " ", text).strip(" -")
        for variant in {text, camel_split(text)}:
            if distinctive(variant, dictionary):
                add(category, variant)

    for workbook in sorted((ROOT / "data" / "raw").glob("*/*.xlsx")):
        wb = openpyxl.load_workbook(workbook, read_only=True)
        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            header = [str(h or "") for h in next(rows)]
            col = {h: i for i, h in enumerate(header)}

            # Competition name: the common start of the "Advanced to ..." headers.
            names = [m.group(1) for h in header if (m := re.search(r'Advanced to "([^"]+)"', h))]
            if names:
                prefix = os.path.commonprefix(names)
                if any(len(n) > len(prefix) and n[len(prefix)].isalnum() for n in names):
                    prefix = prefix.rsplit(" ", 1)[0]
                prefix = re.split(r"\s\d{4}\b|,", prefix)[0].strip()
                if prefix:
                    add("institution", prefix)
                    for w in words_of(prefix):
                        if w.lower() not in GENERIC:
                            add("institution", w)
                    initials = "".join(w[0] for w in words_of(prefix)).upper()
                    if len(initials) >= 3:
                        add("institution", initials)

            for row in rows:
                def cell(name):
                    i = col.get(name)
                    return row[i] if i is not None and i < len(row) else None

                for header_name in ("Name", "Judge Name"):
                    name = cell(header_name)
                    if name and len(words_of(str(name))) >= 2:
                        add("person", name)
                for header_name in ("Email", "Judge Email"):
                    email = cell(header_name)
                    if email:
                        email = str(email).strip()
                        add("email", email)
                        label = domain_label(email.rsplit("@", 1)[-1])
                        if label and label not in MAIL_PROVIDERS and len(label) >= 3:
                            add("institution", label)
                if cell("Entry"):
                    entries[str(cell("Entry"))] += 1
                for i, h in enumerate(header):
                    value = row[i] if i < len(row) else None
                    if not isinstance(value, str):
                        continue
                    if "website" in h.lower():
                        for host in URL_HOST.findall(value):
                            label = domain_label(host)
                            if (label and label not in COMMON_SITES and label not in MAIL_PROVIDERS
                                    and len(label) >= 4):
                                add("venture", label)
                    for url, file_name in HYPERLINK.findall(value):
                        label = domain_label(urlparse(url).hostname or "")
                        if label and label not in COMMON_SITES:
                            add("institution", label)
                        for field in re.split(r"_| - ", file_name):
                            add_name_field("file_name", field)

    for path in (ROOT / "data" / "raw").rglob("*"):
        if path.is_file() and path.suffix.lower() in {".pdf", ".doc", ".docx"}:
            for field in re.split(r"_| - ", path.name):
                add_name_field("file_name", field)

    # Venture names repeated across many applications are form placeholders.
    for entry, count in entries.items():
        if count <= 5:
            add_name_field("venture", entry)

    PRIVATE.mkdir(parents=True, exist_ok=True)
    with open(TERMS, "w") as f:
        for category, term in sorted(terms):
            f.write(f"{category}\t{term}\n")
    ALLOW.touch()
    counts = {}
    for category, _ in terms:
        counts[category] = counts.get(category, 0) + 1
    print(f"wrote {len(terms)} terms to {TERMS.relative_to(ROOT)}: {counts}")


def load_allow(allow_list):
    """An allow list's phrases, one per line: text the check passes over, in any case."""
    allow_list = Path(allow_list)
    if not allow_list.exists():
        return []
    return [re.compile(re.escape(l.strip()), re.I) for l in allow_list.read_text().splitlines() if l.strip()]


def load_patterns(terms=None, allow_list=None):
    """The term list's patterns and the allow list's phrases: the real records' by
    default, or another dataset's, such as the synthetic competition's."""
    terms = Path(terms or TERMS)
    allow = load_allow(allow_list or ALLOW)
    patterns, seen = [], set()
    if terms.exists():
        for line in terms.read_text().splitlines():
            category, term = line.split("\t", 1)
            if term.lower() in seen:
                continue
            seen.add(term.lower())
            body = r"\s+".join(re.escape(w) for w in term.split())
            # Underscores separate words here, as in file names.
            patterns.append((category, term, re.compile(rf"(?<![^\W_])(?<!@){body}(?![^\W_])(?!@)", re.I)))
    return patterns, allow


def mask(text):
    return text[0] + "*" * (len(text) - 1) if text else text


# Whole words as the patterns delimit them: runs of letters and digits.
WORD = re.compile(r"[^\W_]+")
# The characters that the patterns' case-insensitive matching takes for an ASCII letter.
AS_ASCII = {"\u0130": "i", "\u0131": "i", "\u017f": "s", "\u212a": "k"}
# A combining mark that this matching takes for a letter, iota; a text or term with it skips the word test.
LETTER_MARK = "\u0345"


def word_key(word):
    """A key that is equal for any two words the patterns match case-insensitively as equal: ASCII letters
    in lower case, AS_ASCII as the letter it stands for, and every other character as "?"."""
    if word.isascii():
        return word.lower()
    return "".join(AS_ASCII.get(c) or (c.lower() if c.isascii() else "?") for c in word)


def word_keys(text):
    return {word_key(w) for w in set(WORD.findall(text))}


@functools.cache
def term_keys(term):
    return frozenset(word_keys(term))


def scan(label, text, patterns, allow, show):
    found = 0
    # A pattern can match only where every word of its term occurs as a whole word. Testing that on the
    # whole text, then on each line, leaves out nearly every pattern before its regular expression runs,
    # which matters on large files such as stored model outputs. The test finds the same matches as running
    # every pattern on every line (tests/test_sensitive_scan.py).
    test = LETTER_MARK not in text
    candidate = lambda term, words: not test or LETTER_MARK in term or term_keys(term) <= words
    words = word_keys(text) if test else None
    patterns = [p for p in patterns if candidate(p[1], words)]
    for n, line in enumerate(text.splitlines(), start=1):
        for rx in allow:
            line = rx.sub(lambda m: " " * len(m.group(0)), line)
        hits = [("email", m.group(0)) for m in EMAIL.finditer(line) if not EXAMPLE_EMAIL.search(m.group(0))]
        line_words = word_keys(line) if test else None
        hits += [(category, m.group(0)) for category, term, rx in patterns if candidate(term, line_words)
                 for m in rx.finditer(line)]
        for category, match in hits:
            found += 1
            print(f"{label}:{n}: {category}: {match if show else mask(match)}")
    return found


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def check(args):
    patterns, allow = load_patterns()
    if not patterns:
        print("warning: no term list; run `check_sensitive.py build` after downloading the data."
              " Only email addresses are checked.", file=sys.stderr)
    sources = []
    if args.message:
        sources.append((args.message, Path(args.message).read_bytes()))
    elif args.staged:
        for path in git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").decode().split("\0"):
            if path:
                sources.append((path, git("show", f":{path}")))
    elif args.history:
        for commit in git("rev-list", "--all").decode().split():
            sources.append((f"{commit[:7]} (message)", git("log", "-1", "--format=%B", commit)))
            for path in git("ls-tree", "-r", "--name-only", "-z", commit).decode().split("\0"):
                if path:
                    sources.append((f"{commit[:7]}:{path}", git("show", f"{commit}:{path}")))
    else:
        for path in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").decode().split("\0"):
            if path and (ROOT / path).is_file():
                sources.append((path, (ROOT / path).read_bytes()))

    found = 0
    for label, data in sources:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        found += scan(label, text, patterns, allow, args.show)
    if found:
        print(f"{found} possible sensitive terms found. Remove them, or list false positives"
              f" in {ALLOW.relative_to(ROOT)}.", file=sys.stderr)
        sys.exit(1)
    print(f"no sensitive terms found in {len(sources)} files or messages")


def install_hooks():
    hooks = Path(git("rev-parse", "--git-path", "hooks").decode().strip())
    hooks = hooks if hooks.is_absolute() else ROOT / hooks
    hooks.mkdir(parents=True, exist_ok=True)
    for name, command in (("pre-commit", "check --staged"), ("commit-msg", 'check --message "$1"')):
        hook = hooks / name
        hook.write_text(f'#!/bin/sh\nexec uv run --quiet python scripts/check_sensitive.py {command}\n')
        hook.chmod(0o755)
        print(f"installed {hook}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    p = sub.add_parser("check")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--history", action="store_true")
    p.add_argument("--message")
    p.add_argument("--show", action="store_true")
    sub.add_parser("install-hooks")
    args = parser.parse_args()
    {"build": lambda: build(), "check": lambda: check(args), "install-hooks": install_hooks}[args.command]()


if __name__ == "__main__":
    main()
