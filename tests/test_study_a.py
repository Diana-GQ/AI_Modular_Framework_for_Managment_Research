"""Study A's validators, on simulated data with known answers."""

import numpy as np
import pandas as pd
import pytest

from components.shared import stats
from pipeline.runner import Component


def simulate_judging(seed=0, entries=300, judges=80, k=3, var_entry=1.0, var_judge=0.3, var_residual=0.7):
    rng = np.random.default_rng(seed)
    quality = rng.normal(0, var_entry ** 0.5, entries)
    severity = rng.normal(0, var_judge ** 0.5, judges)
    rows = []
    for e in range(entries):
        for j in rng.choice(judges, size=k, replace=False):
            score = 6 + quality[e] + severity[j] + rng.normal(0, var_residual ** 0.5)
            for q in ("Q2", "Q4", "Q6", "Q7", "Q9", "weighted"):
                rows.append({"entry": f"E-{e:06d}", "judge": f"J-{j:06d}", "question": q, "score": float(score)})
    return rows


def test_icc1_matches_textbook_example():
    # Shrout & Fleiss (1979), Table 2: six targets, four judges; ICC(1,1) = .17 and ICC(1,4) = .44.
    table = [[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]]
    result = stats.icc1(table)
    assert result["icc1_single"] == pytest.approx(0.17, abs=0.01)
    assert result["icc1_mean"] == pytest.approx(0.44, abs=0.01)


def test_human_benchmark_recovers_variance_components():
    out = Component("human_benchmark").run({"scores": simulate_judging()}).outputs["by_criterion"]["concept"]
    share = out["share"]
    assert share["entry"] == pytest.approx(0.5, abs=0.1)
    assert share["judge"] == pytest.approx(0.15, abs=0.08)
    assert share["residual"] == pytest.approx(0.35, abs=0.08)
    assert out["reliability_mean_of_3"] > out["reliability_one_judge"]
    assert 0.3 < out["one_judge_vs_other_two"]["pearson"] < 0.8


def simulate_ai(seed=1, entries=120, judges=60, ai_noise=0.3):
    """Human judges with severity and noise, and an AI that sees quality with little noise."""
    rng = np.random.default_rng(seed)
    quality = rng.normal(0, 1, entries)
    severity = rng.normal(0, 0.6, judges)
    human, ai = [], []
    for e in range(entries):
        code = f"E-{e:06d}"
        for j in rng.choice(judges, size=3, replace=False):
            s = float(6 + quality[e] + severity[j] + rng.normal(0, 1))
            human += [{"entry": code, "judge": f"J-{j:06d}", "question": q, "score": s}
                      for q in ("Q2", "Q4", "Q6", "Q7", "Q9", "weighted")]
        for run in range(1, 6):
            s = float(5 + quality[e] + rng.normal(0, ai_noise))
            ai += [{"entry": code, "run": run, "question": q, "score": s} for q in ("Q2", "Q4", "Q6", "Q7", "Q9", "weighted")]
    return human, ai


def test_score_agreement_finds_a_less_noisy_ai_closer_to_the_panel():
    human, ai = simulate_ai()
    out = Component("score_agreement").run({"human": human, "ai": ai}).outputs
    w = out["by_criterion"]["weighted_score"]
    assert w["vs_other_two"]["ai_mean_of_runs"]["pearson"] > w["vs_other_two"]["one_judge"]["pearson"]
    assert w["vs_other_two"]["difference_ai_mean_minus_one_judge"]["low"] > 0
    assert w["mean_difference"] == pytest.approx(-1.0, abs=0.3)
    assert w["run_consistency"]["icc1_single"] > 0.8


def test_ranking_comparison_on_a_less_noisy_ai():
    human, ai = simulate_ai(seed=2)
    weighted_h = [{k: r[k] for k in ("entry", "judge", "score")} for r in human if r["question"] == "weighted"]
    weighted_a = [{k: r[k] for k in ("entry", "run", "score")} for r in ai if r["question"] == "weighted"]
    advanced = [{"entry": f"E-{e:06d}", "advanced": e % 4 == 0} for e in range(120)]
    out = Component("ranking_comparison").run({"human": weighted_h, "ai": weighted_a, "advanced": advanced}).outputs
    a2, a3 = out["rankings_and_selection"], out["expectations"]
    assert a2["selected"] == 30 and a2["rank_correlation"]["spearman"] > 0.5
    assert len(a2["would_gain"]) == len(a2["would_lose"])
    assert a3["cutoff"]["mean_absolute_rank_difference"]["difference"] < 0


def synthetic_vectors(tmp_path, entries=20, dim=32, seed=3):
    """Feedback that shares its entry's direction, and summaries along the same direction."""
    from pipeline.store import Store

    rng = np.random.default_rng(seed)
    base = rng.normal(size=(entries, dim))
    rows, vecs = [], []
    for e in range(entries):
        for source, runs in (("human", 3), ("claude_judge", 2)):
            for r in range(runs):
                v = base[e] + rng.normal(scale=0.8, size=dim)
                rows.append({"id": f"E-{e:06d}|{source}-{r}|Q1|{r + 1}", "source": source, "entry": f"E-{e:06d}",
                             "question": "Q1", "run": r + 1, "words": 50 if source == "human" else 500})
                vecs.append(v / np.linalg.norm(v))
    summaries = base / np.linalg.norm(base, axis=1, keepdims=True)

    def put(matrix):
        import io
        buf = io.BytesIO()
        np.save(buf, np.asarray(matrix, dtype=np.float32), allow_pickle=False)
        return Store().put_file(buf.getvalue(), ".npy")

    return rows, put(vecs), put(summaries), [f"E-{e:06d}|summary" for e in range(entries)]


def test_feedback_comparison_on_synthetic_vectors(tmp_path):
    rows, fv, sv, sids = synthetic_vectors(tmp_path)
    c = Component("feedback_comparison")
    settings_sources = c.settings["sources"]
    out = c.run({"feedback": rows, "feedback_vectors": fv, "feedback_ids": [r["id"] for r in rows],
                 "summary_vectors": sv, "summary_ids": sids}).outputs
    q = out["same_issues"]["Q1"]
    assert q["human~human"]["specificity"] > 0.2 and q["human~claude_judge"]["specificity"] > 0.2
    assert out["fit_to_summary"]["Q1"]["human"]["own_ranked_first"] > 0.5
    assert out["words"]["Q1"]["claude_judge"] == 500
    assert "qwen_judge" in settings_sources


def test_embedding_agreement_is_one_for_identical_embedders(tmp_path):
    rows, fv, _, _ = synthetic_vectors(tmp_path)
    ids = [r["id"] for r in rows]
    out = Component("embedding_agreement").run({"matrices": [
        {"embedder": "a", **fv, "ids": ids}, {"embedder": "b", **fv, "ids": ids}]}).outputs["agreement"]
    assert out["spearman"]["a~b"] == pytest.approx(1.0)


def test_feedback_text_keeps_names_out(tmp_path):
    from tests import synthetic

    terms = tmp_path / "terms.tsv"
    terms.write_text("person\tJane Rivera\nventure\tUmbrellify\n")
    rows = []
    for e in range(8):
        rows.append({"id": f"E-{e}|J|Q1|1", "source": "human", "entry": f"E-{e}", "question": "Q1",
                     "text": "Great idea, I think it may work. Promising concept."})
        rows.append({"id": f"E-{e}|claude_judge|Q1|1", "source": "claude_judge", "entry": f"E-{e}", "question": "Q1",
                     "text": "The defensibility is weak; Rivera and Umbrellify lack a moat. Defensibility matters. Jane Rivera leads."})
    for q in ("Q3", "Q5", "Q8", "Q10"):
        rows += [dict(r, id=r["id"].replace("Q1", q), question=q) for r in rows if r["question"] == "Q1"]
    for e in range(8):
        rows.append({"id": f"E-{e}|qwen_judge|Q1|1", "source": "qwen_judge", "entry": f"E-{e}", "question": "Q1", "text": "Fine."})
    out = Component("feedback_text").run({"feedback": rows, "terms": synthetic.file_ref(terms)}).outputs
    words = out["distinguishing_words"]["Q1"]["claude_judge"]
    ai_words = [w["word"] for w in words["ai"]]
    assert "defensibility" in ai_words and "moat" in ai_words
    assert not {"rivera", "jane", "umbrellify"} & set(ai_words)
    assert "great" in [w["word"] for w in words["human"]]
    assert out["measures"]["human"]["Q1"]["hedges_per_100_words"] > 0
