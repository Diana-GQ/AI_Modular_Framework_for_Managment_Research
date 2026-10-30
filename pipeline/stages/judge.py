"""Plan tasks 3.3 and 3.4: run the AI judges.

    uv run python -m pipeline.stages.judge pilot 2019 [claude|qwen|both]
    uv run python -m pipeline.stages.judge determinism 2019
    uv run python -m pipeline.stages.judge report 2019
    uv run python -m pipeline.stages.judge full 2019 [claude|qwen|both]
    uv run python -m pipeline.stages.judge full-report 2019

The pilot runs both judges on 20 judged summaries drawn with a fixed seed: ten
questions, five runs each, 1,000 calls per judge. Stored answers are never
asked again, so an interrupted run resumes where it stopped. The determinism
test sends the open-weight judge the pilot's 200 prompts of run 1 one at a time,
in one batch, in a shuffled batch, and in one batch to a new container, and
compares the output tokens with the pilot's. The report gives counts, costs and
the checks of task 3.3; the answers themselves go only to a review file for
the authors, data/reports/<year>_pilot_review.md.

The full run (task 3.4) asks every judged summary's ten questions five times.
Before the open-weight judge runs, the pilot's 200 prompts must again give the
pilot's tokens. The full report counts what is stored and missing, and writes
every AI answer to data/tables/<year>/evaluations_ai.parquet, in the form of
the evaluations table, with its status and configuration hash.
"""

import json
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict

import pandas as pd

from ..paths import data_dir
from ..runner import Component, RunError
from .common import reports_dir, write_report

QUESTIONS = [f"Q{i}" for i in range(1, 11)]
SCORES = ("Q2", "Q4", "Q6", "Q7", "Q9")
RUNS = range(1, 6)
PILOT_SIZE = 20
H100_PER_SECOND = 0.001097  # Modal's list price on 2026-10-12, US dollars
TOPIC = {"Q1": r"concept|idea|need|pain|problem|offering", "Q3": r"business model|revenue|pric|scal|monet|margin",
         "Q5": r"market|customer|segment|exit", "Q8": r"summary|writ|submission|clarity|section|format",
         "Q10": r"strength|weakness"}


def summaries(year: int) -> dict[str, str]:
    """Each judged entry's summary text, by entry code."""
    folder = data_dir() / "tables" / str(year)
    entries = pd.read_parquet(folder / "entries.parquet")
    documents = pd.read_parquet(folder / "documents.parquet")
    judged = set(entries.loc[entries["judged"], "entry"])
    return {r.entry: r.text for r in documents.itertuples() if r.entry in judged}


def pilot_entries(year: int) -> list[str]:
    path = reports_dir() / f"{year}_pilot_entries.json"
    if path.exists():
        return json.loads(path.read_text())
    chosen = sorted(random.Random(year).sample(sorted(summaries(year)), PILOT_SIZE))
    path.write_text(json.dumps(chosen, indent=1) + "\n")
    return chosen


def calls(texts: dict[str, str], entries: list[str], runs=RUNS, questions=QUESTIONS) -> list[dict]:
    return [{"entry": e, "summary": texts[e], "question": q, "run": r} for e in entries for q in questions for r in runs]


def run_configs(year: int, label: str, record: dict | None = None) -> dict[str, str]:
    """The configuration hash each judge ran under in a given run ("pilot" or
    "full"), recorded when the run starts, so that its answers stay readable
    after a later change gives a component a new configuration."""
    path = reports_dir() / f"{year}_{label}_configs.json"
    configs = json.loads(path.read_text()) if path.exists() else {}
    if record:
        configs.update(record)
        path.write_text(json.dumps(configs, indent=1) + "\n")
    return configs


def pilot_configs(year: int, record: dict | None = None) -> dict[str, str]:
    return run_configs(year, "pilot", record)


def failures(results) -> list[str]:
    return [r.error for r in results if isinstance(r, RunError)]


def run_claude(year, texts, entries, label="pilot", workers=8, group=1) -> None:
    """A few summaries at a time: first one written and one score call per
    summary, so that each summary's text is cached, then the remaining calls in
    parallel. A group finishes well within the cache's five minutes."""
    claude = Component("claude_judge")
    run_configs(year, label, {"claude_judge": claude.config_hash})
    for n in range(0, len(entries), group):
        chunk = entries[n:n + group]
        batch = calls(texts, chunk)
        first = [c for c in batch if c["run"] == 1 and c["question"] in ("Q1", "Q2")]
        rest = [c for c in batch if c not in first]
        results = claude.run_batch(first, workers=2 * len(chunk)) + claude.run_batch(rest, workers=workers)
        statuses = Counter(r.outputs["status"] for r in results if not isinstance(r, RunError))
        errors = failures(results)
        print(f"claude {min(n + group, len(entries))}/{len(entries)}: {dict(statuses)}"
              + (f"; {len(errors)} failed: {errors[0][:120]}" if errors else ""), flush=True)


def log_session(year: int, name: str, session: dict, ended: float, **extra) -> None:
    path = reports_dir() / f"{year}_qwen_sessions.json"
    log = json.loads(path.read_text()) if path.exists() else []
    log.append({"name": name, "seconds": round(ended - session["started"], 1),
                "environment": session["environment"], **extra})
    path.write_text(json.dumps(log, indent=1) + "\n")


def run_qwen(year, texts, entries, label="pilot", chunk=500, precheck=False) -> None:
    qwen = Component("qwen_judge")
    run_configs(year, label, {"qwen_judge": qwen.config_hash})
    pending = [c for c in calls(texts, entries) if qwen.cached(c) is None]
    if not pending:
        print("qwen: every answer is stored")
        return
    with qwen.module.session(qwen.settings) as session:
        if precheck and not determinism_precheck(year, session):
            log_session(year, f"{label}, stopped: determinism check failed", session, time.time(), calls=0)
            sys.exit("the deployment does not reproduce the pilot's outputs; nothing was run")
        for i in range(0, len(pending), chunk):
            results = qwen.run_batch(pending[i:i + chunk])
            print(f"qwen {min(i + chunk, len(pending))}/{len(pending)}: "
                  f"{dict(Counter(r.outputs['status'] for r in results))}", flush=True)
        log_session(year, label, session, time.time(), calls=len(pending))


def pilot_requests(year: int) -> tuple[list[dict], list[list[int]]]:
    """The pilot's 200 prompts of run 1, as sent, and the output tokens they gave."""
    qwen = Component("qwen_judge")
    reference = stored(qwen, calls(summaries(year), pilot_entries(year), runs=[1]), pilot_configs(year)["qwen_judge"])
    if any(d is None for _, _, d in reference):
        sys.exit("run the open-weight pilot first")
    return [d["request"] for _, _, d in reference], [d["response"]["token_ids"] for _, _, d in reference]


def determinism_precheck(year: int, session: dict) -> bool:
    """Before an experiment: the pilot's 200 prompts in one batch must give the pilot's tokens."""
    requests, tokens = pilot_requests(year)
    fresh = [r["token_ids"] for r in session["judge"].generate.remote(requests)]
    identical = sum(a == b for a, b in zip(tokens, fresh))
    write_report(f"{year}_determinism_precheck.json", {"prompts": len(requests), "identical_to_pilot": identical,
                                                       "passed": identical == len(requests)})
    print(f"determinism check: {identical}/{len(requests)} identical to the pilot", flush=True)
    return identical == len(requests)


def stored(component: Component, batch: list[dict], config_hash: str) -> list[tuple[dict, dict | None, dict | None]]:
    """(inputs, outputs, provenance details) for each call stored under the
    given configuration; None where nothing is stored."""
    name, out = component.contract.component, []
    for c in batch:
        entry = component.store.lookup(name, config_hash, component._prepare(c)[1])
        if entry is None:
            out.append((c, None, None))
        else:
            out.append((c, component.store.get(entry["output"]), component.store.get_record(name, entry["record"])["details"]))
    return out


def determinism(year: int) -> None:
    qwen = Component("qwen_judge")
    requests, pilot_tokens = pilot_requests(year)
    tokens = {"pilot": pilot_tokens}
    order = list(range(len(requests)))
    random.Random(year).shuffle(order)
    with qwen.module.session(qwen.settings) as session:
        tokens["one_at_a_time"] = [session["judge"].generate.remote([r])[0]["token_ids"] for r in requests]
        tokens["one_batch"] = [r["token_ids"] for r in session["judge"].generate.remote(requests)]
        shuffled = session["judge"].generate.remote([requests[i] for i in order])
        unshuffled = [None] * len(order)
        for position, i in enumerate(order):
            unshuffled[i] = shuffled[position]["token_ids"]
        tokens["shuffled_batch"] = unshuffled
        log_session(year, "determinism", session, time.time(), calls=3 * len(requests))
    with qwen.module.session(qwen.settings) as session:
        tokens["new_container"] = [r["token_ids"] for r in session["judge"].generate.remote(requests)]
        log_session(year, "determinism, new container", session, time.time(), calls=len(requests))
    modes = {m: sum(a == b for a, b in zip(tokens["pilot"], t)) for m, t in tokens.items() if m != "pilot"}
    report = {"prompts": len(requests), "identical_to_pilot": modes,
              "passed": all(v == len(requests) for v in modes.values()),
              "compared": "output token IDs", "pilot": "the pilot's batches of up to 500 requests"}
    write_report(f"{year}_determinism.json", report)
    print(json.dumps(report, indent=1))


def icc1(matrix: list[list[float]]) -> float | None:
    """One-way intraclass correlation, ICC(1): summaries in rows, runs in columns."""
    n, k = len(matrix), len(matrix[0])
    if n < 2:
        return None
    grand = statistics.fmean(x for row in matrix for x in row)
    means = [statistics.fmean(row) for row in matrix]
    msb = k * sum((m - grand) ** 2 for m in means) / (n - 1)
    msw = sum((x - m) ** 2 for row, m in zip(matrix, means) for x in row) / (n * (k - 1))
    denominator = msb + (k - 1) * msw
    return round((msb - msw) / denominator, 3) if denominator else None


def summarize(name: str, rows) -> dict:
    done = [(c, o, d) for c, o, d in rows if o is not None]
    statuses = Counter(o["status"] for _, o, _ in done)
    out = {"planned": len(rows), "stored": len(done), "statuses": dict(statuses),
           "share_ok": round(statuses.get("ok", 0) / len(rows), 4)}
    by_q = defaultdict(list)
    for c, o, d in done:
        by_q[c["question"]].append((c, o, d))
    out["scores"] = {}
    for q in SCORES:
        table = defaultdict(dict)
        for c, o, _ in by_q[q]:
            if o["score"] is not None:
                table[c["entry"]][c["run"]] = o["score"]
        complete = [list(v.values()) for v in table.values() if len(v) == len(RUNS)]
        values = [x for row in complete for x in row]
        out["scores"][q] = {
            "mean": round(statistics.fmean(values), 2) if values else None,
            "distribution": dict(sorted(Counter(values).items())),
            "icc1_across_runs": icc1(complete) if complete else None,
            "summaries_with_identical_runs": sum(len(set(row)) == 1 for row in complete)}
    out["written"] = {}
    for q in TOPIC:
        answers = [o["answer"] for _, o, _ in by_q[q] if o["answer"]]
        words = [len(a.split()) for a in answers]
        out["written"][q] = {
            "answers": len(answers),
            "words": {"min": min(words), "median": statistics.median(words), "max": max(words)} if words else None,
            "share_on_topic": round(sum(bool(re.search(TOPIC[q], a, re.I)) for a in answers) / len(answers), 3) if answers else None}
    q10 = [o["answer"] for _, o, _ in by_q["Q10"] if o["answer"]]
    number = r"\b(10|[1-9])\s*(/|out of)\s*10\b|\b(rating|score|interest) (of|at|is|:)\s*(10|[1-9])\b|\brated? (it |this )?(an? )?(10|[1-9])\b"
    share = lambda pattern: round(sum(bool(re.search(pattern, a, re.I)) for a in q10) / len(q10), 3) if q10 else None
    out["q10"] = {
        "share_naming_strengths_and_weaknesses": round(sum(bool(re.search(r"strength", a, re.I) and re.search(r"weakness", a, re.I)) for a in q10) / len(q10), 3) if q10 else None,
        "share_mentioning_a_rating": share(r"\brat(ing|ed)\b"),
        "share_stating_a_number_as_its_rating": share(number)}
    if name == "claude":
        usage = Counter()
        for _, _, d in done:
            usage.update({k: v for k, v in d["usage"].items() if isinstance(v, int)})
        cost = sum(d["cost_usd"] for _, _, d in done)
        seconds = [d["seconds"] for _, _, d in done]
        prompt = usage["input_tokens"] + usage["cache_read_input_tokens"] + usage["cache_creation_input_tokens"]
        out["usage"] = {k: usage[k] for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
        out["share_of_prompt_tokens_from_cache"] = round(usage["cache_read_input_tokens"] / prompt, 3) if prompt else None
        out["cost_usd"] = round(cost, 2)
        out["cost_per_call_usd"] = round(cost / len(done), 5) if done else None
        out["seconds_per_call"] = {"median": round(statistics.median(seconds), 1), "max": round(max(seconds), 1)} if seconds else None
    else:
        prompt = sum(d["response"]["prompt_tokens"] for _, _, d in done)
        output = sum(d["response"]["output_tokens"] for _, _, d in done)
        out["usage"] = {"prompt_tokens": prompt, "output_tokens": output}
    return out


def report(year: int) -> None:
    texts = summaries(year)
    entries = pilot_entries(year)
    batch = calls(texts, entries)
    result = {"year": year, "pilot_summaries": len(entries), "calls_per_judge": len(batch),
              "judged_summaries": len(texts), "full_run_calls_per_judge": len(texts) * len(QUESTIONS) * len(RUNS)}
    rows, configs = {}, pilot_configs(year)
    result["configurations"] = configs
    for name, component in (("claude", "claude_judge"), ("qwen", "qwen_judge")):
        rows[name] = stored(Component(component), batch, configs[component])
        result[name] = summarize(name, rows[name])
    sessions_path = reports_dir() / f"{year}_qwen_sessions.json"
    sessions = json.loads(sessions_path.read_text()) if sessions_path.exists() else []
    # The sessions up to the pilot's report only: the log goes on to record the full run.
    sessions = [s for s in sessions if not s["name"].startswith("full")]
    gpu_seconds = sum(s["seconds"] for s in sessions)
    result["qwen"]["gpu_sessions"] = [{k: s[k] for k in ("name", "seconds", "calls")} for s in sessions]
    result["qwen"]["gpu_cost_usd_estimate"] = round(gpu_seconds * H100_PER_SECOND, 2)
    if result["claude"].get("cost_per_call_usd"):
        result["projection_full_run_usd"] = {
            "claude": round(result["claude"]["cost_per_call_usd"] * result["full_run_calls_per_judge"], 0),
            "claude_with_batch_interface": round(result["claude"]["cost_per_call_usd"] * result["full_run_calls_per_judge"] / 2, 0)}
    pilot = [s for s in sessions if s["name"] == "pilot"]
    if pilot:
        per_call = sum(s["seconds"] for s in pilot) / sum(s["calls"] for s in pilot)
        result.setdefault("projection_full_run_usd", {})["qwen_upper_bound"] = round(per_call * result["full_run_calls_per_judge"] * H100_PER_SECOND, 0)
    write_report(f"{year}_pilot.json", result)
    review(year, entries[:3], rows)
    print(json.dumps(result, indent=1))


def review(year: int, entries: list[str], rows: dict) -> None:
    """Both judges' run 1 answers for a few summaries, for the authors to read."""
    lines = [f"# Pilot answers for review, {year}", "",
             "Run 1 of both judges for three pilot summaries. Read each summary in "
             f"data/tables/{year}/documents.parquet (or the original file) alongside. "
             "Check that each answer addresses its question, and that the Q10 answers make sense "
             "although the model gave no rating in the same call.", ""]
    for entry in entries:
        lines += [f"## {entry}", ""]
        for q in QUESTIONS:
            lines.append(f"### {q}")
            for name in ("claude", "qwen"):
                o = next((o for c, o, _ in rows[name] if c["entry"] == entry and c["question"] == q and c["run"] == 1), None)
                value = "(not run)" if o is None else o["answer"] if o["answer"] else o["score"] if o["score"] is not None else o["status"]
                lines.append(f"- **{name}:** {value}")
            lines.append("")
    (reports_dir() / f"{year}_pilot_review.md").write_text("\n".join(lines))


def full_report(year: int) -> None:
    """Task 3.4: every planned answer stored with its provenance, or recorded as
    missing, and the AI answers exported in the evaluations table's form."""
    folder = data_dir() / "tables" / str(year)
    entries = pd.read_parquet(folder / "entries.parquet")
    texts = summaries(year)
    judged = sorted(entries.loc[entries["judged"], "entry"])
    configs = run_configs(year, "full")
    result = {"year": year, "judged_entries": len(judged), "judged_summaries": len(texts),
              "planned_per_judge": len(judged) * len(QUESTIONS) * len(RUNS), "configurations": configs}
    rows = []
    for name, component in (("claude", "claude_judge"), ("qwen", "qwen_judge")):
        c = Component(component)
        found = stored(c, calls(texts, sorted(texts)), configs[component])
        statuses = Counter(o["status"] if o else "not stored" for _, o, _ in found)
        missing_summary = (len(judged) - len(texts)) * len(QUESTIONS) * len(RUNS)
        result[name] = {"stored": sum(o is not None for _, o, _ in found), "statuses": dict(statuses),
                        "missing_no_summary": missing_summary}
        if name == "claude":
            result[name]["cost_usd"] = round(sum(d["cost_usd"] for _, _, d in found if d), 2)
        for inputs, o, d in found:
            rows.append({"year": year, "entry": inputs["entry"], "evaluator": component, "evaluator_type": "ai",
                         "question": inputs["question"], "run": inputs["run"],
                         "score": float(o["score"]) if o and o["score"] is not None else None,
                         "text": o["answer"] if o else None, "status": o["status"] if o else "not stored",
                         "config_hash": configs[component]})
        for entry in sorted(set(judged) - set(texts)):
            for q in QUESTIONS:
                for r in RUNS:
                    rows.append({"year": year, "entry": entry, "evaluator": component, "evaluator_type": "ai",
                                 "question": q, "run": r, "score": None, "text": None, "status": "no summary",
                                 "config_hash": configs[component]})
    # The open-weight judge re-executed the pilot's calls under the final configuration: same tokens?
    qwen = Component("qwen_judge")
    pilot_batch = calls(texts, pilot_entries(year))
    before = stored(qwen, pilot_batch, pilot_configs(year)["qwen_judge"])
    after = stored(qwen, pilot_batch, configs["qwen_judge"])
    result["qwen"]["pilot_calls_identical_in_full_run"] = sum(
        a[2] is not None and b[2] is not None and a[2]["response"]["token_ids"] == b[2]["response"]["token_ids"]
        for a, b in zip(before, after))
    claude = Component("claude_judge")
    before = stored(claude, pilot_batch, pilot_configs(year)["claude_judge"])
    after = stored(claude, pilot_batch, configs["claude_judge"])
    same = [a[1]["score"] == b[1]["score"] for a, b in zip(before, after)
            if a[1] and b[1] and a[1]["score"] is not None and b[1]["score"] is not None]
    result["claude"]["pilot_scores_equal_in_full_run"] = f"{sum(same)} of {len(same)}"
    sessions_path = reports_dir() / f"{year}_qwen_sessions.json"
    sessions = json.loads(sessions_path.read_text()) if sessions_path.exists() else []
    result["qwen"]["gpu_seconds_full_run"] = round(sum(s["seconds"] for s in sessions if s["name"].startswith("full")), 1)
    pd.DataFrame(rows).to_parquet(folder / "evaluations_ai.parquet", index=False)
    write_report(f"{year}_full_run.json", result)
    print(json.dumps(result, indent=1))


def main() -> None:
    command, year = sys.argv[1], int(sys.argv[2])
    if command == "pilot":
        which = sys.argv[3] if len(sys.argv) > 3 else "both"
        texts = summaries(year)
        entries = pilot_entries(year)
        print(f"pilot: {len(entries)} of {len(texts)} judged summaries")
        if which in ("claude", "both"):
            run_claude(year, texts, entries)
        if which in ("qwen", "both"):
            run_qwen(year, texts, entries)
    elif command == "full":
        which = sys.argv[3] if len(sys.argv) > 3 else "both"
        texts = summaries(year)
        entries = sorted(texts)
        print(f"full run: {len(entries)} judged summaries")
        if which in ("claude", "both"):
            run_claude(year, texts, entries, label="full", workers=12, group=3)
        if which in ("qwen", "both"):
            run_qwen(year, texts, entries, label="full", precheck=True)
    elif command == "full-report":
        full_report(year)
    elif command == "determinism":
        determinism(year)
    elif command == "report":
        report(year)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
