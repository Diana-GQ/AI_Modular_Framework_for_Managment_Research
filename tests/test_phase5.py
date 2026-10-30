"""Phase 5's measures and analyses, on synthetic data with known answers."""

import io

import numpy as np
import pytest

from pipeline.runner import Component
from pipeline.store import Store


def put(matrix):
    buf = io.BytesIO()
    np.save(buf, np.asarray(matrix, dtype=np.float32), allow_pickle=False)
    return Store().put_file(buf.getvalue(), ".npy")


def test_venture_characteristics():
    entries = [
        {"entry": "E-1", "company_type": "Internet and Consumer Technology", "product_type": "Software/App | Service",
         "fields": "Health | Apps", "milestones": "Core business concept defined | First client has paid",
         "entity_formed": True, "entity_type": "We formed an LLC.", "has_website": True},
        {"entry": "E-2", "company_type": "Non-Internet and Consumer Technology ( everything else)", "product_type": "Physical Product",
         "fields": "Health", "milestones": None, "entity_formed": False, "entity_type": None, "has_website": False},
    ]
    c = Component("venture_characteristics")
    out = c.run({"entries": entries}).outputs
    rows = {r["entry"]: r for r in out["characteristics"]}
    assert rows["E-1"]["internet_consumer_tech"] is True and rows["E-2"]["internet_consumer_tech"] is False
    assert rows["E-1"]["product_software_app"] and rows["E-1"]["product_service"] and not rows["E-1"]["product_physical_product"]
    assert rows["E-1"]["milestones_reached"] == 2 and rows["E-1"]["milestone_first_client_has_paid"]
    assert rows["E-1"]["entity_category"] == "llc" and rows["E-2"]["entity_category"] == "none_stated"
    assert "entity_type" not in rows["E-1"]  # the free text is not kept
    assert out["common_fields"] == []  # no field reaches the threshold of ten entries


def test_style_profiler():
    text = "We may perhaps sell 100 umbrellas. We clearly must sell them. Our plan is simple."
    out = Component("style_profiler").run({"documents": [{"entry": "E-1", "text": text, "pages": 3}]}).outputs["profile"][0]
    assert out["words"] == 14 and out["sentences"] == 3  # "100" is a number, not a word
    assert out["over_page_limit"] is True
    assert out["hedges_per_100_words"] == pytest.approx(100 * 2 / 14)
    assert out["boosters_per_100_words"] == pytest.approx(100 * 2 / 14)
    assert out["we_per_100_words"] == pytest.approx(100 * 3 / 14)
    assert out["numbers_per_100_words"] == pytest.approx(100 * 1 / 14)


def clustered_vectors(seed=0, groups=4, per=10, dim=24, noise=0.3):
    rng = np.random.default_rng(seed)
    centres = rng.normal(size=(groups, dim))
    x = np.vstack([centres[g] + rng.normal(scale=noise, size=(per, dim)) for g in range(groups)])
    x[-1] = rng.normal(size=dim) * 3  # one outlier, far from every group
    return x, [f"E-{i:03d}|summary" for i in range(len(x))]


def test_novelty_ranks_the_outlier_first():
    x, ids = clustered_vectors()
    out = Component("novelty").run({"embedder": "embedder_qwen3", "vectors": put(x), "ids": ids}).outputs
    scores = {r["entry"]: r["novelty"] for r in out["scores"]}
    assert max(scores, key=scores.get) == "E-039"


def test_novelty_composite():
    rows = [{"embedder": e, "entry": f"E-{i}", "novelty": float(i + (j * 0.1 if i % 2 else 0))}
            for j, e in enumerate(["embedder_bge_m3", "embedder_gte_modernbert", "embedder_qwen3"]) for i in range(10)]
    out = Component("novelty_composite").run({"scores": rows}).outputs
    comp = {r["entry"]: r["novelty"] for r in out["composite"]}
    assert comp["E-9"] > comp["E-0"]
    assert out["agreement"]["mean_spearman_between_embedders"] == pytest.approx(1.0)


def test_topics_and_their_agreement(tmp_path):
    from tests import synthetic

    x, ids = clustered_vectors(groups=4, per=12, dim=24, noise=0.2)
    terms = tmp_path / "terms.tsv"
    terms.write_text("person\tJane Rivera\n")
    docs = [{"entry": i.split("|")[0], "text": f"Our product serves group{int(i[2:5]) // 12} customers well. Jane Rivera leads."} for i in ids]
    c = Component("topics")
    out = c.run({"embedder": "embedder_qwen3", "vectors": put(x), "ids": ids, "documents": docs, "terms": synthetic.file_ref(terms)}).outputs
    assert out["topics"] in (4, 5)
    words = [w for ws in out["words"].values() for w in ws]
    assert not {"jane", "rivera"} & set(words)
    assigned = [{"embedder": e, **a} for e in ("a", "b") for a in out["assignments"]]
    agreement = Component("topic_agreement").run({"assignments": assigned}).outputs
    assert agreement["adjusted_rand"]["a~b"] == pytest.approx(1.0)


def test_similarity_known_groups_passes_when_categories_track_similarity():
    rng = np.random.default_rng(1)
    entries, cats, vecs = [], [], []
    base = {"A": rng.normal(size=16), "B": rng.normal(size=16)}
    for i in range(30):
        g = "A" if i < 15 else "B"
        entries.append(f"E-{i:03d}")
        cats.append({"entry": f"E-{i:03d}", "fields": "Health | Apps" if g == "A" else "Energy | Cleantech",
                     "product_type": "Software/App" if g == "A" else "Physical Product"})
        v = base[g] + rng.normal(scale=0.5, size=16)
        vecs.append(v / np.linalg.norm(v))
    sim = np.array(vecs) @ np.array(vecs).T
    ids = [f"{e}|summary" for e in entries]
    out = Component("similarity_known_groups").run({"matrices": [{"embedder": "x", **put(sim), "ids": ids}], "categories": cats}).outputs
    v = out["by_embedder"]["x"]
    assert v["passed"] and v["difference"] > 0 and v["spearman_with_category_overlap"] > 0.5


def simulated_outcomes(seed=2, n=134):
    rng = np.random.default_rng(seed)
    words = rng.integers(400, 1600, n)
    paid = rng.random(n) < 0.3
    quality = rng.normal(size=n)
    human = 6 + quality + 0.8 * paid + rng.normal(scale=1, size=n)
    claude = 5 + quality + 0.8 * (np.log(words) - np.log(words).mean()) + rng.normal(scale=0.5, size=n)
    outcomes, features = [], []
    for i in range(n):
        e = f"E-{i:03d}"
        outcomes.append({"entry": e, "human": float(human[i]), "claude": float(claude[i]), "qwen": float(claude[i] + rng.normal()),
                         "advanced": bool(human[i] > np.quantile(human, 0.72))})
        features.append({"entry": e, "log_words": float(np.log(words[i])), "flesch_reading_ease": float(rng.normal(37, 9)),
                         "hedges_per_100_words": float(rng.random()), "boosters_per_100_words": float(rng.random()),
                         "numbers_per_100_words": float(rng.random() * 5), "we_per_100_words": float(rng.random() * 3),
                         "internet_consumer_tech": bool(rng.random() < 0.5), "product_software_app": bool(rng.random() < 0.5),
                         "product_physical_product": bool(rng.random() < 0.4), "product_data_analytics": bool(rng.random() < 0.3),
                         "product_service": bool(rng.random() < 0.3), "milestones_reached": int(rng.integers(1, 6)),
                         "milestone_first_client_has_paid": bool(paid[i]), "milestone_funding_raised": bool(rng.random() < 0.2),
                         "entity_formed": bool(rng.random() < 0.6), "has_website": bool(rng.random() < 0.6)})
    return outcomes, features


def test_score_explanation_finds_form_for_the_ai_and_substance_for_the_judges():
    outcomes, features = simulated_outcomes()
    c = Component("score_explanation")
    c.settings["bootstrap_reps"] = 200
    out = c.module.run({"outcomes": outcomes, "features": features}, c.settings)
    assert out["coefficients"]["claude"]["log_words"]["low"] > 0
    assert out["coefficients"]["human"]["milestone_first_client_has_paid"]["low"] > 0
    assert out["explained"]["claude"]["form"] > out["explained"]["human"]["form"]
    assert out["advancement"]["linear_probability"]["human_score"]["coefficient"] > 0


def test_novelty_profile_bins():
    outcomes, _ = simulated_outcomes()
    novelty = [{"entry": o["entry"], "novelty": float(i)} for i, o in enumerate(outcomes)]
    out = Component("novelty_profile").run({"outcomes": outcomes, "novelty": novelty}).outputs
    assert len(out["by_bin"]) == 5 and sum(b["entries"] for b in out["by_bin"]) == 134
    assert "not validated" in out["note"]
