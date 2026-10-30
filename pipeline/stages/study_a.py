"""Plan Phase 4: Study A, first pass (design, Section 4).

    uv run python -m pipeline.stages.study_a benchmark 2019    # 4.1 the human benchmark
    uv run python -m pipeline.stages.study_a agreement 2019    # 4.2 A1: scores, consistency, halo
    uv run python -m pipeline.stages.study_a rankings 2019     # 4.3 A2 and A3
    uv run python -m pipeline.stages.study_a embed 2019        # 4.4 the embedders, on Modal
    uv run python -m pipeline.stages.study_a embed-check 2019  # 4.4 the embedders, re-executed
    uv run python -m pipeline.stages.study_a feedback 2019     # 4.4 A4: feedback
    uv run python -m pipeline.stages.study_a report 2019       # the first report
    uv run python -m pipeline.stages.study_a measures 2019     # 5.1 characteristics, style, novelty, topics
    uv run python -m pipeline.stages.study_a explain 2019      # 5.3 A5: what explains the scores

Each analysis is a component, so each number in the report has a provenance
record. Claude is the AI judge of the main tests; the open-weight judge repeats
them as a check (design, B3).
"""

import sys

import pandas as pd

from ..paths import data_dir
from ..runner import Component

JUDGES = ("claude_judge", "qwen_judge")
SCORE_QUESTIONS = ("Q2", "Q4", "Q6", "Q7", "Q9")


def tables(year: int) -> dict[str, pd.DataFrame]:
    folder = data_dir() / "tables" / str(year)
    return {name: pd.read_parquet(folder / f"{name}.parquet")
            for name in ("entries", "documents", "evaluations", "judges", "evaluations_ai")}


def human_scores(t: dict) -> list[dict]:
    ev = t["evaluations"]
    ev = ev[(ev["evaluator_type"] == "human") & ev["question"].isin([*SCORE_QUESTIONS, "weighted"])]
    return [{"entry": r.entry, "judge": r.evaluator, "question": r.question, "score": float(r.score)}
            for r in ev.sort_values(["entry", "evaluator", "question"]).itertuples()]


def benchmark(year: int):
    result = Component("human_benchmark").run({"scores": human_scores(tables(year))})
    return result


def ai_scores(t: dict, judge: str) -> list[dict]:
    """One AI judge's scores by entry, run and question, with each run's weighted
    score computed by the weighted score component (so it has its provenance)."""
    ai = t["evaluations_ai"]
    ai = ai[(ai["evaluator"] == judge) & (ai["status"] == "ok") & ai["question"].isin(SCORE_QUESTIONS)]
    wide = ai.pivot_table(index=["entry", "run"], columns="question", values="score")
    names = {"Q2": "concept", "Q4": "business_model", "Q6": "market", "Q7": "written_work", "Q9": "investor_interest"}
    weighted = Component("weighted_score").run_batch(
        [{"scores": {names[q]: float(row[q]) for q in SCORE_QUESTIONS}} for _, row in wide.iterrows()])
    rows = [{"entry": r.entry, "run": int(r.run), "question": r.question, "score": float(r.score)}
            for r in ai.sort_values(["entry", "run", "question"]).itertuples()]
    rows += [{"entry": entry, "run": int(run), "question": "weighted", "score": res.outputs["weighted_score"]}
             for (entry, run), res in zip(wide.index, weighted)]
    return rows


def agreement(year: int) -> dict:
    t = tables(year)
    human = human_scores(t)
    return {judge: Component("score_agreement").run({"human": human, "ai": ai_scores(t, judge)}) for judge in JUDGES}


def rankings(year: int) -> dict:
    """A2 and A3 use the AI judges' scores in tests, so the methodological check
    must pass first: each judge validated, with a reliability estimate."""
    from ..checks import assert_ready_for_inference

    t = tables(year)
    ev = t["evaluations"]
    human = [{"entry": r.entry, "judge": r.evaluator, "score": float(r.score)}
             for r in ev[(ev["evaluator_type"] == "human") & (ev["question"] == "weighted")].sort_values(["entry", "evaluator"]).itertuples()]
    e = t["entries"]
    advanced = [{"entry": r.entry, "advanced": bool(r.advanced_r2)} for r in e[e["judged"]].sort_values("entry").itertuples()]
    out = {}
    for judge in JUDGES:
        assert_ready_for_inference(Component(judge).contract)
        ai = [{"entry": r["entry"], "run": r["run"], "score": r["score"]} for r in ai_scores(t, judge) if r["question"] == "weighted"]
        out[judge] = Component("ranking_comparison").run({"human": human, "ai": ai, "advanced": advanced})
    return out


EMBEDDERS = ("embedder_qwen3", "embedder_bge_m3", "embedder_gte_modernbert")
WRITTEN = ("Q1", "Q3", "Q5", "Q8", "Q10")


def feedback_texts(t: dict) -> list[dict]:
    """The written feedback of the judges and of both AI judges, on the five
    written questions, with ids of the form entry|evaluator|question|run."""
    rows = []
    ev = t["evaluations"]
    for r in ev[(ev["evaluator_type"] == "human") & ev["question"].isin(WRITTEN)].itertuples():
        rows.append({"id": f"{r.entry}|{r.evaluator}|{r.question}|1", "source": "human", "entry": r.entry,
                     "evaluator": r.evaluator, "question": r.question, "run": 1, "text": r.text})
    ai = t["evaluations_ai"]
    for r in ai[(ai["status"] == "ok") & ai["question"].isin(WRITTEN)].itertuples():
        rows.append({"id": f"{r.entry}|{r.evaluator}|{r.question}|{r.run}", "source": r.evaluator, "entry": r.entry,
                     "evaluator": r.evaluator, "question": r.question, "run": int(r.run), "text": r.text})
    return sorted(rows, key=lambda r: r["id"])


def summary_texts(t: dict) -> list[dict]:
    return sorted(({"id": f"{r.entry}|summary", "text": r.text} for r in t["documents"].itertuples()), key=lambda r: r["id"])


def embed(year: int) -> dict:
    t = tables(year)
    sets = {"feedback": [{"id": r["id"], "text": r["text"]} for r in feedback_texts(t)], "summaries": summary_texts(t)}
    out = {}
    for name in EMBEDDERS:
        for label, rows in sets.items():
            out[(name, label)] = result = Component(name).run({"texts": rows})
            print(f"{name} {label}: {len(rows)} texts, dimension {result.outputs['dimension']}, "
                  f"truncated {result.outputs['truncated']}" + (" (reused)" if result.cached else ""), flush=True)
    return out


def embed_check(year: int) -> dict:
    """Re-execution: the summaries embedded again, in a new container, must give
    bit-identical matrices. The rerun is recorded beside the stored output."""
    from .common import write_report

    t = tables(year)
    rows = summary_texts(t)
    out = {}
    for name in EMBEDDERS:
        c = Component(name)
        first = c.run({"texts": rows})
        again = c.run({"texts": rows}, rerun=True)
        out[name] = {"texts": len(rows), "identical": first.outputs["vectors"]["sha256"] == again.outputs["vectors"]["sha256"],
                     "first": first.outputs["vectors"]["sha256"], "again": again.outputs["vectors"]["sha256"]}
        print(name, "identical" if out[name]["identical"] else "DIFFERENT", flush=True)
    write_report(f"{year}_embedding_reexecution.json", out)
    return out


def feedback(year: int) -> dict:
    from ..checks import assert_comparable
    from .common import file_ref

    t = tables(year)
    rows = feedback_texts(t)
    meta = [{"id": r["id"], "source": r["source"], "entry": r["entry"], "question": r["question"], "run": r["run"],
             "words": len(r["text"].split())} for r in rows]
    vectors = {key: result.outputs for key, result in embed(year).items()}
    out = {}
    for name in EMBEDDERS:
        spec = Component(name).contract.typed.outputs["vectors"]
        assert_comparable(spec, spec)  # feedback and summaries: the same embedder, so the same type
        f, s = vectors[(name, "feedback")], vectors[(name, "summaries")]
        out[name] = Component("feedback_comparison").run({
            "feedback": meta, "feedback_vectors": f["vectors"], "feedback_ids": f["ids"],
            "summary_vectors": s["vectors"], "summary_ids": s["ids"]})
    for label in ("feedback", "summaries"):
        out[f"agreement:{label}"] = Component("embedding_agreement").run({"matrices": [
            {"embedder": name, **vectors[(name, label)]["vectors"], "ids": vectors[(name, label)]["ids"]} for name in EMBEDDERS]})
    out["text"] = Component("feedback_text").run({
        "feedback": [{k: r[k] for k in ("id", "source", "entry", "question", "text")} for r in rows],
        "terms": file_ref(data_dir() / "private" / "sensitive_terms.tsv")})
    return out


def measures(year: int) -> dict:
    """Plan task 5.1: the ventures' characteristics, the style and language
    profile, and novelty and topics from each embedder's vectors."""
    from .common import file_ref

    t = tables(year)
    e = t["entries"]
    cols = ["entry", "company_type", "product_type", "fields", "milestones", "entity_formed", "entity_type", "has_website"]
    entries = [{c: (None if pd.isna(v) else v) for c, v in zip(cols, row)} for row in e[e["judged"]][cols].itertuples(index=False)]
    out = {"characteristics": Component("venture_characteristics").run({"entries": entries})}
    docs = [{"entry": r.entry, "text": r.text, "pages": None if pd.isna(r.pages) else int(r.pages)} for r in t["documents"].sort_values("entry").itertuples()]
    out["style"] = Component("style_profiler").run({"documents": docs})
    terms = file_ref(data_dir() / "private" / "sensitive_terms.tsv")
    vecs = embed(year)
    assignments = []
    for name in EMBEDDERS:
        v = vecs[(name, "summaries")].outputs
        out[f"novelty:{name}"] = Component("novelty").run({"embedder": name, "vectors": v["vectors"], "ids": v["ids"]})
        out[f"topics:{name}"] = topics = Component("topics").run({
            "embedder": name, "vectors": v["vectors"], "ids": v["ids"],
            "documents": [{"entry": d["entry"], "text": d["text"]} for d in docs], "terms": terms})
        assignments += [{"embedder": name, **a} for a in topics.outputs["assignments"]]
    out["topic_agreement"] = Component("topic_agreement").run({"assignments": assignments})
    out["novelty"] = Component("novelty_composite").run({"scores": [
        {"embedder": name, "entry": r["entry"], "novelty": r["novelty"]}
        for name in EMBEDDERS for r in out[f"novelty:{name}"].outputs["scores"]]})
    return out


def explain(year: int) -> dict:
    """Plan task 5.3, A5. The AI judges' scores, the style profile and the
    ventures' characteristics enter regressions, so the methodological check
    must pass for each; novelty, without human validation, is only described."""
    import numpy as np

    from ..checks import MethodError, assert_ready_for_inference

    for name in (*JUDGES, "style_profiler", "venture_characteristics"):
        assert_ready_for_inference(Component(name).contract)
    t = tables(year)
    m = measures(year)
    ev = t["evaluations"]
    human = ev[(ev["evaluator_type"] == "human") & (ev["question"] == "weighted")].groupby("entry")["score"].mean()
    ai = {j: pd.DataFrame([r for r in ai_scores(t, j) if r["question"] == "weighted"]).groupby("entry")["score"].mean() for j in JUDGES}
    e = t["entries"].set_index("entry")
    entries = sorted(set(human.index) & set(ai["claude_judge"].index))
    outcomes = [{"entry": x, "human": float(human[x]), "claude": float(ai["claude_judge"][x]), "qwen": float(ai["qwen_judge"][x]),
                 "advanced": bool(e.loc[x, "advanced_r2"])} for x in entries]
    style = pd.DataFrame(m["style"].outputs["profile"]).set_index("entry")
    style["log_words"] = np.log(style["words"])
    chars = pd.DataFrame(m["characteristics"].outputs["characteristics"]).set_index("entry")
    feats = style.join(chars, how="inner").reindex(entries)
    cols = Component("score_explanation").settings
    keep = cols["form"] + cols["substance"]
    features = [{"entry": x, **{c: (None if pd.isna(feats.loc[x, c]) else (bool(feats.loc[x, c]) if isinstance(feats.loc[x, c], (bool, np.bool_)) else float(feats.loc[x, c]))) for c in keep}}
                for x in entries]
    out = {"explanation": Component("score_explanation").run({"outcomes": outcomes, "features": features})}
    try:
        assert_ready_for_inference(Component("novelty_composite").contract)
        raise RuntimeError("novelty is validated: add it to the regressions instead of describing it")
    except MethodError:
        pass  # As expected: novelty is described, not tested.
    out["novelty"] = Component("novelty_profile").run({"outcomes": outcomes, "novelty": m["novelty"].outputs["composite"]})
    return out


def report(year: int) -> None:
    import json

    from .common import reports_dir
    from .study_a_report import write

    path = reports_dir() / f"{year}_embedding_reexecution.json"
    reexec = json.loads(path.read_text()) if path.exists() else None
    meas = measures(year)
    t = tables(year)
    e = t["entries"]
    categories = [{"entry": r.entry, "fields": r.fields if isinstance(r.fields, str) else None,
                   "product_type": r.product_type if isinstance(r.product_type, str) else None}
                  for r in e[e["judged"] & e["entry"].isin(set(t["documents"]["entry"]))].sort_values("entry").itertuples()]
    meas["known_groups"] = Component("similarity_known_groups").run({"matrices": [
        {"embedder": n, **meas[f"novelty:{n}"].outputs["similarity"], "ids": meas[f"novelty:{n}"].outputs["ids"]} for n in EMBEDDERS],
        "categories": categories})
    judged = set(e.loc[e["judged"], "entry"]) & set(t["documents"]["entry"])
    text = write(year, benchmark(year), agreement(year), rankings(year), feedback(year), reexec, meas, explain(year), summaries=len(judged))
    out = reports_dir() / f"{year}_study_a_report.md"
    out.write_text(text)
    print(f"report: {out.relative_to(data_dir().parent)}")


def main() -> None:
    command, year = sys.argv[1], int(sys.argv[2])
    if command == "benchmark":
        import json
        r = benchmark(year)
        print(json.dumps(r.outputs, indent=1)[:6000])
    elif command == "agreement":
        for judge, r in agreement(year).items():
            print(judge, "stored output", r.output_sha[:12], "(reused)" if r.cached else "")
    elif command == "rankings":
        for judge, r in rankings(year).items():
            print(judge, "stored output", r.output_sha[:12], "(reused)" if r.cached else "")
    elif command == "embed":
        embed(year)
    elif command == "embed-check":
        embed_check(year)
    elif command == "measures":
        for key, r in measures(year).items():
            print(key, "stored output", r.output_sha[:12], "(reused)" if r.cached else "", flush=True)
    elif command == "explain":
        for key, r in explain(year).items():
            print(key, "stored output", r.output_sha[:12], "(reused)" if r.cached else "", flush=True)
    elif command == "report":
        report(year)
    elif command == "feedback":
        for key, r in feedback(year).items():
            print(key, "stored output", r.output_sha[:12], "(reused)" if r.cached else "")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
