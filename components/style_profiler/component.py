"""Plan task 5.1: the style and language profiler (design, Section 3): length,
compliance with the two-page limit, readability, hedging and boosting
(Hyland 2005), quantification and the voice of the team, for each summary.
Code only: no model is involved."""

import re

import textstat

TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*")
NUMBER = re.compile(r"\d[\d,.]*%?|\$\s?\d|%")


def per_100(count: int, words: int) -> float:
    return 100 * count / words if words else 0.0


def count_terms(words: list[str], terms: list[str]) -> int:
    single = {t for t in terms if " " not in t}
    joined = " " + " ".join(words) + " "
    return sum(w in single for w in words) + sum(joined.count(f" {t} ") for t in terms if " " in t)


def run(inputs: dict, settings: dict) -> dict:
    textstat.set_lang("en")
    rows = []
    for d in inputs["documents"]:
        text = d["text"]
        words = [w.lower() for w in TOKEN.findall(text)]
        n = len(words)
        sentences = max(1, textstat.sentence_count(text))
        rows.append({
            "entry": d["entry"], "words": n, "sentences": sentences,
            "words_per_sentence": n / sentences,
            "flesch_reading_ease": float(textstat.flesch_reading_ease(text)),
            "flesch_kincaid_grade": float(textstat.flesch_kincaid_grade(text)),
            "pages": d["pages"],
            "over_page_limit": None if d["pages"] is None else d["pages"] > settings["page_limit"],
            "hedges_per_100_words": per_100(count_terms(words, settings["hedges"]), n),
            "boosters_per_100_words": per_100(count_terms(words, settings["boosters"]), n),
            "numbers_per_100_words": per_100(len(NUMBER.findall(text)), n),
            "we_per_100_words": per_100(sum(w in {"we", "our", "us", "ours"} for w in words), n),
        })
    return {"profile": sorted(rows, key=lambda r: r["entry"])}
