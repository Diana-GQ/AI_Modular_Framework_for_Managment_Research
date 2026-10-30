"""Plan task 4.4, analysis A4 through text analysis (design, Section 4): the
length, hedging and tone of each source's feedback on each question, and the
words that most distinguish human from AI feedback, by the log-odds ratio with
an informative Dirichlet prior (Monroe, Colaresi & Quinn 2008).

So that no name can surface, a distinguishing word must appear in feedback on
at least `min_entries` different entries, must not be capitalized in most of
its occurrences that do not start a sentence, and must not be a word of any
name in the private term list."""

import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]+")


def excluded_words(terms_path: str) -> set:
    words = set()
    for line in Path(terms_path).read_text().splitlines():
        category, term = line.split("\t", 1)
        parts = [w.lower() for w in TOKEN.findall(term)]
        if category == "person" or len(parts) == 1:
            words.update(parts)
    return words


def hedges_per_100(text: str, single: set, multi: list) -> float:
    words = [w.lower() for w in TOKEN.findall(text)]
    if not words:
        return 0.0
    count = sum(w in single for w in words)
    joined = " " + " ".join(words) + " "
    count += sum(joined.count(f" {m} ") for m in multi)
    return 100 * count / len(words)


def log_odds(a: Counter, b: Counter, prior: float) -> dict:
    vocab = set(a) | set(b)
    na, nb = sum(a.values()), sum(b.values())
    total = na + nb
    out = {}
    for w in vocab:
        alpha = prior * (a[w] + b[w]) / total
        da = np.log((a[w] + alpha) / (na + prior - a[w] - alpha))
        db = np.log((b[w] + alpha) / (nb + prior - b[w] - alpha))
        out[w] = float((da - db) / np.sqrt(1 / (a[w] + alpha) + 1 / (b[w] + alpha)))
    return out


def run(inputs: dict, settings: dict) -> dict:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    fb = pd.DataFrame(inputs["feedback"])
    stop = set(Path(__file__).resolve().parent.parent.joinpath("shared", "stopwords.txt").read_text().split())
    banned = excluded_words(inputs["terms"]["path"])
    single = {h for h in settings["hedges"] if " " not in h}
    multi = [h for h in settings["hedges"] if " " in h]
    vader = SentimentIntensityAnalyzer()
    fb["words"] = fb["text"].map(lambda t: len(TOKEN.findall(t)))
    fb["hedges"] = fb["text"].map(lambda t: hedges_per_100(t, single, multi))
    fb["tone"] = fb["text"].map(lambda t: vader.polarity_scores(t)["compound"])

    measures = {}
    for (source, q), g in fb.groupby(["source", "question"]):
        measures.setdefault(source, {})[q] = {
            "texts": int(len(g)), "mean_words": float(g["words"].mean()), "median_words": float(g["words"].median()),
            "hedges_per_100_words": float(g["hedges"].mean()), "tone": float(g["tone"].mean()),
            "share_positive": float((g["tone"] >= 0.05).mean()), "share_negative": float((g["tone"] <= -0.05).mean())}

    def tokens(texts):
        """Counts, and how often each word is capitalized where a sentence does not start."""
        counts, capital, inner, entries = Counter(), Counter(), Counter(), {}
        for entry, text in texts:
            seen = set()
            for m in TOKEN.finditer(text):
                w, lw = m.group(0), m.group(0).lower()
                if len(lw) < 3 or lw in stop:
                    continue
                counts[lw] += 1
                before = text[:m.start()].rstrip()
                if before and before[-1] not in ".!?:;\n\"'(*-":
                    inner[lw] += 1
                    capital[lw] += w[0].isupper()
                seen.add(lw)
            for lw in seen:
                entries.setdefault(lw, set()).add(entry)
        return counts, capital, inner, entries

    distinguishing = {}
    for q in settings["questions"]:
        h = fb[(fb["source"] == "human") & (fb["question"] == q)]
        hc, hcap, hin, hent = tokens(zip(h["entry"], h["text"]))
        for source in settings["ai_sources"]:
            a = fb[(fb["source"] == source) & (fb["question"] == q)]
            ac, acap, ain, aent = tokens(zip(a["entry"], a["text"]))
            z = log_odds(hc, ac, settings["prior"])

            def keep(w, ents):
                inner = hin[w] + ain[w]
                proper = inner and (hcap[w] + acap[w]) / inner > 0.5
                return len(ents.get(w, ())) >= settings["min_entries"] and w not in banned and not proper

            # Ties are broken alphabetically: the order of a set changes from one run to the next.
            human_side = [w for w, v in sorted(z.items(), key=lambda x: (-x[1], x[0])) if v > 0 and keep(w, hent)]
            ai_side = [w for w, v in sorted(z.items(), key=lambda x: (x[1], x[0])) if v < 0 and keep(w, aent)]
            n = settings["top_words"]
            distinguishing.setdefault(q, {})[source] = {
                "human": [{"word": w, "z": round(z[w], 2)} for w in human_side[:n]],
                "ai": [{"word": w, "z": round(z[w], 2)} for w in ai_side[:n]]}
    return {"measures": measures, "distinguishing_words": distinguishing}
