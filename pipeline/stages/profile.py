"""Plan task 2.5: profile a year's records, in counts only.

    uv run python -m pipeline.stages.profile 2019

Reads the analysis tables (data/tables/<year>/) and reports missing values,
duplicates, the structure of the judging, the weighted scores recomputed by
the weighted score component, and the advancement pattern of the design's
Section 1.2. Duplicate applications are counted from the export, where the team
lead's email address identifies them; no address leaves this script.
"""

import json
import statistics
import sys
from collections import Counter

import pandas as pd
from openpyxl import load_workbook

from ..paths import data_dir
from ..runner import Component
from .common import workbook, write_report

CRITERIA = {"Q2": "concept", "Q4": "business_model", "Q6": "market", "Q7": "written_work", "Q9": "investor_interest"}
TEXTS = ("Q1", "Q2c", "Q3", "Q5", "Q8", "Q10")


def tables(year: int) -> dict[str, pd.DataFrame]:
    folder = data_dir() / "tables" / str(year)
    return {name: pd.read_parquet(folder / f"{name}.parquet") for name in ("entries", "documents", "evaluations", "judges")}


def duplicate_applications(year: int) -> int:
    """Applications whose team lead's email address appears on an earlier application."""
    rows = list(load_workbook(workbook(year))["Worksheet"].iter_rows(values_only=True))
    col = [str(h or "").strip() for h in rows[0]].index("Email")
    emails = Counter(str(r[col]).strip().lower() for r in rows[1:] if r[col])
    return sum(n - 1 for n in emails.values() if n > 1)


def main(year: int) -> None:
    t = tables(year)
    entries, documents, evaluations = t["entries"], t["documents"], t["evaluations"]
    human = evaluations[evaluations["evaluator_type"] == "human"]
    report = {"year": year}

    in_sheet = entries[entries["submitted"].notna()]
    report["applications"] = {
        "started": len(in_sheet), "submitted": int(in_sheet["submitted"].sum()),
        "judged": int(entries["judged"].sum()),
        "judged_missing_from_applications_sheet": int((entries["judged"] & entries["submitted"].isna()).sum()),
        "judged_not_marked_submitted": int((entries["judged"] & (entries["submitted"] == False)).sum()),  # noqa: E712
        "submitted_not_judged": int((entries["submitted"] == True).sum() - (entries["judged"] & (entries["submitted"] == True)).sum()),  # noqa: E712
        "advanced_r2": int(entries["advanced_r2"].fillna(False).sum()),
        "advanced_r2_not_judged": int((entries["advanced_r2"].fillna(False) & ~entries["judged"]).sum()),
        "duplicate_applications_same_team_lead": duplicate_applications(year),
        "missing_form_answers_among_submitted": {
            c: int(in_sheet.loc[in_sheet["submitted"] == True, c].isna().sum())  # noqa: E712
            for c in ("pitch", "description", "product_type", "company_type", "fields", "milestones", "entity_formed")},
    }

    per_judge = human.groupby("evaluator")["entry"].nunique()
    per_entry = human.groupby("entry")["evaluator"].nunique()
    per_eval = human.groupby(["entry", "evaluator"])["question"].apply(set)
    report["judging"] = {
        "evaluations": int(len(per_eval)), "judged_entries": int(human["entry"].nunique()),
        "judges": int(human["evaluator"].nunique()),
        "evaluations_per_entry": {int(k): int(v) for k, v in Counter(per_entry).items()},
        "evaluations_per_judge": {"min": int(per_judge.min()), "median": float(per_judge.median()), "max": int(per_judge.max())},
        "evaluations_missing_a_score": int(sum(not set(CRITERIA) <= q for q in per_eval)),
        "evaluations_missing_a_required_text": int(sum(not set(TEXTS) - {"Q2c"} <= q for q in per_eval)),
        "optional_concept_comment_missing": int(sum("Q2c" not in q for q in per_eval)),
        "scores_outside_1_to_10": int(((human["score"] < 1) | (human["score"] > 10))[human["question"].isin(list(CRITERIA))].sum()),
        "mean_words_per_text": {q: round(human.loc[human["question"] == q, "text"].str.split().str.len().mean(), 1) for q in TEXTS},
    }

    # Weighted scores, recomputed by the weighted score component and compared with the recorded ones.
    wide = human.pivot_table(index=["entry", "evaluator"], columns="question", values="score", aggfunc="first")
    batch = [{"scores": {name: float(row[q]) for q, name in CRITERIA.items()}} for _, row in wide.iterrows()]
    recomputed = [r.outputs["weighted_score"] for r in Component("weighted_score").run_batch(batch)]
    wide["recomputed"] = recomputed
    report["weighted_score"] = {"evaluations": len(wide),
                                "max_abs_difference_from_recorded": float((wide["recomputed"] - wide["weighted"]).abs().max())}

    # Rank: is it the dense rank of the entry's mean weighted score?
    mean = wide.groupby("entry")["recomputed"].mean().round(6)
    ranks = entries.set_index("entry")["r1_rank"].dropna()
    dense = mean.rank(ascending=False, method="dense")
    report["rank"] = {"entries": int(len(ranks)), "distinct": int(ranks.nunique()),
                      "equal_to_dense_rank_of_mean_weighted_score": int((dense.reindex(ranks.index) == ranks).sum())}

    # Advancement (design, Section 1.2): position = 1 + entries with a strictly higher mean weighted score.
    judged = entries[entries["judged"]].set_index("entry")
    position = mean.apply(lambda m: int((mean > m).sum()) + 1)
    advanced = judged["advanced_r2"].fillna(False).astype(bool)
    n_adv = int(advanced.sum())
    worst_advanced = int(position[advanced[advanced].index].max())
    report["advancement"] = {
        "advanced": n_adv,
        "advanced_within_top_n_positions": int((position[advanced[advanced].index] <= n_adv).sum()),
        "top_n_positions_not_advanced": int(((position <= n_adv) & ~advanced.reindex(position.index)).sum()),
        "lowest_position_advanced": worst_advanced,
        "highest_position_not_advanced": int(position[advanced[~advanced].index].min()),
        "not_advanced_above_lowest_advanced": int(((position < worst_advanced) & ~advanced.reindex(position.index)).sum()),
        "judged_entries": int(len(judged)),
    }

    report["documents"] = {
        "summaries": len(documents), "by_type": dict(Counter(documents["file_type"])),
        "entries_with_more_than_one": int((documents.groupby("entry").size() > 1).sum()),
        "identical_files_under_different_entries": int(documents["sha256"].duplicated().sum()),
        "needs_ocr": int(documents["needs_ocr"].sum()),
        "pdf_pages": {int(k): int(v) for k, v in sorted(Counter(documents["pages"].dropna()).items())},
        "pdfs_over_two_pages": int((documents["pages"] > 2).sum()),
        "words": {"min": int(documents["words"].min()), "median": float(documents["words"].median()),
                  "max": int(documents["words"].max())},
        "judged_entries_without_summary": int((entries["judged"] & ~entries["has_summary"]).sum()),
        "summaries_of_unsubmitted_applications": int((entries["has_summary"] & (entries["submitted"] == False)).sum()),  # noqa: E712
        "summaries_of_judged_entries": int((entries["has_summary"] & entries["judged"]).sum()),
    }
    path = write_report(f"{year}_profile.json", report)
    print(json.dumps(report, indent=1, default=str))
    print(f"report: {path.relative_to(data_dir().parent)}")


if __name__ == "__main__":
    main(int(sys.argv[1]))
