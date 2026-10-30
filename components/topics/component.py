"""Plan task 5.1: the topics of the summaries (design, Section 3), as clusters of
one embedder's whitened vectors (Ward linkage), the number of topics chosen by
the mean silhouette; each topic described by its most distinctive words.

So that no name can surface, a word must appear in at least `min_documents`
summaries of the topic, must not be capitalized in most of its occurrences that
do not start a sentence, and must not be a word of a name in the private term list."""

import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

from components.shared import vectors

TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]+")


def silhouette(w: np.ndarray, labels: np.ndarray) -> float:
    d = 1 - w @ w.T
    values = []
    for i in range(len(w)):
        same = labels == labels[i]
        if same.sum() <= 1:
            values.append(0.0)
            continue
        a = d[i, same].sum() / (same.sum() - 1)
        b = min(d[i, labels == c].mean() for c in set(labels) if c != labels[i])
        values.append((b - a) / max(a, b))
    return float(np.mean(values))


def banned_words(path: str) -> set:
    words = set()
    for line in Path(path).read_text().splitlines():
        category, term = line.split("\t", 1)
        parts = [w.lower() for w in TOKEN.findall(term)]
        if category == "person" or len(parts) == 1:
            words.update(parts)
    return words


def run(inputs: dict, settings: dict) -> dict:
    x = vectors.load(inputs["vectors"])
    ids = inputs["ids"]
    w, _ = vectors.whiten(x, settings["whitening_dimensions"])
    tree = linkage(w, method="ward")
    candidates = {k: fcluster(tree, k, criterion="maxclust") for k in range(settings["min_topics"], settings["max_topics"] + 1)}
    scores = {k: silhouette(w, labels) for k, labels in candidates.items()}
    best = max(scores, key=lambda k: (scores[k], -k))
    labels = candidates[best]
    entries = [i.split("|")[0] for i in ids]

    texts = {d["entry"]: d["text"] for d in inputs["documents"]}
    stop = set(Path(__file__).resolve().parent.parent.joinpath("shared", "stopwords.txt").read_text().split())
    banned = banned_words(inputs["terms"]["path"])
    counts, docs, capital, inner = {}, {}, Counter(), Counter()
    for entry, label in zip(entries, labels):
        text = texts[entry]
        c = counts.setdefault(int(label), Counter())
        seen = set()
        for m in TOKEN.finditer(text):
            lw = m.group(0).lower()
            if len(lw) < 3 or lw in stop:
                continue
            c[lw] += 1
            before = text[:m.start()].rstrip()
            if before and before[-1] not in ".!?:;\n\"'(*-":
                inner[lw] += 1
                capital[lw] += m.group(0)[0].isupper()
            seen.add(lw)
        for lw in seen:
            docs.setdefault((int(label), lw), set()).add(entry)
    total = sum(counts.values(), Counter())
    words = {}
    for label, c in counts.items():
        rest = total - c
        nc, nr = sum(c.values()), sum(rest.values())
        prior = settings["prior"]
        z = {}
        for word in c:
            alpha = prior * total[word] / sum(total.values())
            d1 = np.log((c[word] + alpha) / (nc + prior - c[word] - alpha))
            d2 = np.log((rest[word] + alpha) / (nr + prior - rest[word] - alpha))
            z[word] = (d1 - d2) / np.sqrt(1 / (c[word] + alpha) + 1 / (rest[word] + alpha))
        keep = [wd for wd, v in sorted(z.items(), key=lambda kv: -kv[1])
                if v > 0 and len(docs.get((label, wd), ())) >= settings["min_documents"] and wd not in banned
                and not (inner[wd] and capital[wd] / inner[wd] > 0.5)]
        words[str(label)] = keep[:settings["top_words"]]
    return {"assignments": [{"entry": e, "topic": int(t)} for e, t in zip(entries, labels)],
            "topics": int(best), "silhouette": {str(k): v for k, v in scores.items()},
            "sizes": {str(k): int(v) for k, v in sorted(Counter(int(t) for t in labels).items())}, "words": words}
