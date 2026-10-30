"""The first report of Study A (plan, Phase 4), written from the components'
stored outputs, with the provenance of every table. Counts, statistics and
codes only; no text from the summaries or the feedback.

    uv run python -m pipeline.stages.study_a report 2019
"""

import json
from datetime import date

from ..paths import ROOT, data_dir
from ..runner import Component

NAMES = {"concept": "Concept", "business_model": "Business model", "market": "Market", "written_work": "Written work",
         "investor_interest": "Investor interest", "weighted_score": "Weighted score"}
JUDGE_NAMES = {"claude_judge": "Claude Sonnet 5.5", "qwen_judge": "Qwen3-8B"}
QUESTIONS = {"Q1": "Q1 concept", "Q3": "Q3 business model", "Q5": "Q5 market", "Q8": "Q8 written work", "Q10": "Q10 investor interest"}


def f2(x) -> str:
    return "–" if x is None else f"{x:.2f}"


def f3(x) -> str:
    return "–" if x is None else f"{x:.3f}"


def ordered(d: dict) -> list:
    """Criteria in the competition's order, not the store's alphabetical one."""
    return [(k, d[k]) for k in NAMES if k in d]


def ci(d) -> str:
    return f"{d['difference' if 'difference' in d else 'estimate']:+.2f} [{d['low']:+.2f}, {d['high']:+.2f}]"


class Provenance:
    def __init__(self):
        self.rows = []

    def cite(self, label: str, component: str, result) -> str:
        c = Component(component)
        self.rows.append((label, component, c.contract.version, c.config_hash[:12], result.output_sha[:12],
                          result.record_id.split(":")[-1][:8]))
        return f"*Source: `{component}`, configuration `{c.config_hash[:12]}`, output `{result.output_sha[:12]}`.*"

    def table(self) -> list[str]:
        lines = ["| Result | Component | Version | Configuration | Output | Provenance record |", "|---|---|---|---|---|---|"]
        lines += [f"| {a} | `{b}` | {c} | `{d}` | `{e}` | `{f}…` |" for a, b, c, d, e, f in self.rows]
        return lines


ABOUT = [
    "## About this report", "",
    "Study A compares the evaluations of the same executive summaries by the competition's human judges and by two AI judges, to identify where and why the evaluations agree and differ. Three human judges scored each summary from 1 to 10 on five criteria (concept, business model, market, written work, investor interest) and wrote comments. The same questions were posed five times to each AI judge, Claude Sonnet 5.5 and the open-weight Qwen3-8B; each time is a *run*. Claude is the main AI judge; Qwen3-8B is a check that can be re-executed exactly.", "",
    "Terms used throughout:",
    "- *Weighted score*: the competition's overall score of one evaluation, 0.2 × concept + 0.2 × business model + 0.2 × market + 0.1 × written work + 0.3 × investor interest.",
    "- *Correlation* (Pearson's r): how closely two sets of numbers rise and fall together, from −1 to 1, where 0 means no relation. *Spearman's correlation* does the same with ranks.",
    "- *95% interval*: the range of values compatible with the data, from re-running the calculation on 2,000 resamples of the entries (a bootstrap). If it excludes zero, the difference is unlikely to be chance.",
    "- *Standardized*: expressed in standard deviations, which allows measures on different scales to be compared.",
    "",
]


def intro(asks: str, measures: list[str], fits: str) -> list[str]:
    """The opening of a section: what it asks, what its measures mean, and how it fits."""
    return [f"**What it asks.** {asks}", "", "**The measures.**", *[f"- {m}" for m in measures], "", f"**How it fits.** {fits}", ""]


INTRO = {
    "benchmark": intro(
        "How much do the human judges agree with one another? Their agreement is the yardstick for the AI judges: an AI judge whose scores agree with the judges' as closely as the judges' scores agree among themselves performs as well as one more judge.",
        ["*ICC(1), the intraclass correlation*: the share of the variation in scores that reflects real differences between entries rather than disagreement among judges. 0 means the judges agree no more than chance; 1, perfectly. *One judge* is the reliability of a single judge's score; *three*, of the average of three.",
         "*Variance shares*: a statistical model (with crossed random effects for entries and judges) divides the variation in scores into differences between entries, which the scores should capture; each judge's overall severity, some judges scoring everyone higher or lower (*level noise*); and each judge's reactions to particular entries, with any other error (*pattern noise*). Judges were assigned to entries at random; severity is therefore not confounded with the quality of the entries a judge saw.",
         "*One judge vs two*: the correlation between one judge's score and the average of the entry's other two judges, over all three judges of each entry. Section 2 compares the AI judges with this number."],
        "The summary's first point; the benchmark for Sections 2 and 3."),
    "scores": intro(
        "How closely do the AI judges' scores match the human judges'? How consistent are each AI judge's scores across runs? Do the scores of human and AI judges distinguish the five criteria, or treat them all alike?",
        ["*Human mean, AI mean, difference*: average scores over the entries; a negative difference means the AI judge's scores are lower.",
         "*r with human mean*: the correlation between the AI judge's score, averaged over its five runs, and the average of the three judges.",
         "*Judge vs two, AI vs two, one run vs two*: correlations with the average of two judges, for the third judge, for the AI judge's average, and for a single AI run. They put the AI judge and one more human judge on the same footing. *AI minus judge* is the difference, with its 95% interval.",
         "*ICC across runs*: how consistent the AI judge's scores are across its five runs, from 0 to 1. *Same score in all runs*: the share of entries where all five runs gave the same score.",
         "*Halo*: the tendency of one overall impression to colour all five scores, measured by the average correlation among an evaluation's five scores; the *first eigenvalue share* is how much of their variation one general factor captures. The *multitrait-multimethod* comparison tests whether the scores of a criterion agree across humans and AI more than different criteria do; if not, the scores of both mostly reflect one general impression."],
        "The summary's second to fourth points: agreement, score levels and consistency, and halo; findings 1 to 3 in Section 8."),
    "rankings": intro(
        "If the entries were ranked by an AI judge's scores and as many were selected as advanced, would the same entries be selected? Do the evaluations of human and AI judges agree on the strongest entries but diverge near the cutoff for advancing, as the design expected?",
        ["*Rank correlation*: Spearman's and Kendall's correlations between the ranking by the AI judge's scores and the ranking by the judges' (1 is the same order).",
         "*Overlap*: how many entries two selections share, each as large as the number that advanced: the selection by AI scores against those that advanced, and against the judges' own top. Where advancement departs from the judges' ranking, as when entries that missed a requirement of the process are skipped, the judges' own top is the cleaner comparison.",
         "*Would gain, would lose*: entries that a selection by AI scores would include but that did not advance, and the reverse; their median place in the judges' ranking shows where they stand.",
         "*Testing the expectations*: each judge of an entry is held out in turn, and the average of the other two ranks the entries (the *reference*). Among the ten strongest entries by the reference, and among those near the cutoff (within ten places of it), the table compares how far the rank from the AI judge's scores is from the reference with how far the held-out judge's is (*rank difference*, in places), and how often each ranking places an entry on the other side of the cutoff. A negative *AI minus judge* means that the AI judge's ranks are closer to the two judges' than a third judge's are."],
        "The summary's points on selections and the expectations; findings 4 and 5 in Section 8."),
    "feedback": intro(
        "Do the AI judges' written comments discuss the same issues as the human judges' comments on the same entry? Are they more uniform across entries, and tied more closely to the summary? How do they differ in length, hedging, tone and vocabulary?",
        ["*Embeddings and cosine similarity*: an embedding model turns a text into a list of numbers that captures its meaning; the cosine similarity of two such lists runs from about 0 (unrelated) to 1 (the same meaning). Three models from different families are used, and only patterns found with all three are treated as findings.",
         "*Specificity*: the similarity of two comments on the same entry minus that of comments on different entries. It shows whether two sources discuss *this* entry's issues, and is much less affected than raw similarity by the AI judges' far longer texts.",
         "*Alike across entries*: the average similarity of one source's comments on different entries; higher means more uniform, template-like feedback.",
         "*Fit to the summary*: a comment's similarity to its own summary minus its average similarity to the other summaries; *own ranked first* is how often the summary a comment most resembles is its own.",
         "*Embedders' agreement*: the correlation between the three models' similarity patterns over the same texts. *Re-execution*: whether embedding the texts again, in a new container, gives identical numbers.",
         "*Hedges*: words that soften a claim (may, perhaps, seems), per 100 words. *Tone*: a dictionary score of positive against negative wording, from −1 to 1. *Distinctive words*: words much more frequent in one source than in the other, allowing for how common each word is."],
        "The summary's point on feedback; finding 6 in Section 8."),
    "measures": intro(
        "Which measures of the summaries are used to explain the scores in Section 6, and how far can each be trusted without human coders?",
        ["*Style and language*: length; readability (*Flesch reading ease*, where higher is easier and 30 to 50 is college level, and the equivalent school *grade*); hedges and *boosters*, words that strengthen a claim (clearly, must); *numbers*, amounts and percentages; and *we, our, us*, the team speaking in its own voice; all per 100 words.",
         "*Novelty*: how far a summary is in meaning from its five most similar summaries of the year. The three models' scores are averaged into a *composite*; their agreement, and the composite's *reliability* by the Spearman-Brown formula (as for averaging several raters), show how stable it is.",
         "*Known-groups check*: without human ratings, similarity is checked against the teams' own categories. Pairs of ventures that chose at least two of the same fields on the application form should look more similar than pairs with nothing in common. The *standardized difference* is the gap in standard deviations; 0.8 counts as large.",
         "*Topics*: groups of similar summaries. The *silhouette* measures how well separated the groups are (from −1 to 1; near 0 means weak structure), and the *adjusted Rand index* how far the three models' groupings agree (0 is chance, 1 identical)."],
        "The summary's point on the content measures. Novelty and topics have no human validation; they are therefore described, not tested (Section 9)."),
    "explain": intro(
        "Which features of a summary's *form* (length, readability, hedging, numbers, voice) and of the venture's *substance* (products, milestones, legal entity, website) go with higher scores from the judges and from Claude? Which explain where Claude's scores and the judges' disagree, and which predict advancing?",
        ["*Variance explained (R²)*: the share of the differences in scores that the features account for, from 0 to 1, for form alone, substance alone and both; *adjusted* corrects for the number of features. *Form minus substance* compares the two groups, with a 95% interval.",
         "*Divergence*: Claude's standardized score minus the judges'. A feature that raises divergence is associated with relatively higher scores from Claude than from the judges.",
         "*Coefficients*: how many standard deviations the score moves with one standard deviation of a continuous feature, or when a yes-or-no feature is present, holding the other features fixed; 95% intervals robust to unequal variances (HC3). Bold marks intervals that exclude zero.",
         "*Linear probability model*: how each feature changes the probability of advancing, holding the judges' score fixed.",
         "*Novelty profile*: average scores in each fifth of the entries ordered by novelty; a description only, since novelty has no human validation."],
        "The summary's points on form and substance, divergence and advancement; findings 7 to 10 in Section 8."),
}


def synthetic() -> bool:
    """Whether the data are the synthetic competition's (design, B4), which its build marks."""
    return (data_dir() / "synthetic.json").exists()


SYNTHETIC_NOTE = ("**Synthetic data.** This report is on the synthetic competition that the public package carries "
                  "(design, B4): invented ventures, summaries, judges, scores and comments, generated as "
                  "`synthetic/README.md` describes. The judges' scores are simulated with the shares of variance and the halo "
                  "measured on the 2019 judges as targets; with 40 ventures and 15 judges, the shares realized here differ from them by chance "
                  "(Section 1). The AI judges are the real ones. The numbers show the pipeline at work and "
                  "test nothing about real judges.")


def write(year: int, bench, agree: dict, ranks: dict, fb: dict, reexec: dict, meas: dict | None = None, expl: dict | None = None,
          summaries: int | None = None) -> str:
    p = Provenance()
    records = f"the synthetic competition (fictional year {year})" if synthetic() else f"the {year} round 1 records"
    title = f"# Study A: {records}" if expl else f"# Study A, first pass: {records}"
    phases = "Phases 4 and 5" if expl else "Phase 4"
    L = [title, "",
         f"Written {date.today().isoformat()} from the components' stored outputs (plan, {phases}). Exploratory: the analyses of "
         f"{year} suggest findings that further years test (design, Section 7). Counts and statistics only.", ""]
    if synthetic():
        L += [SYNTHETIC_NOTE, ""]
    L += ABOUT

    b = bench.outputs["by_criterion"]
    w = b["weighted_score"]
    ca = agree["claude_judge"].outputs["by_criterion"]["weighted_score"]
    qa = agree["qwen_judge"].outputs["by_criterion"]["weighted_score"]
    cr = ranks["claude_judge"].outputs
    L += ["## Summary", "", *_summary(b, agree, ranks, fb, meas, expl)]
    L.append("")

    # 4.1
    L += ["## 1. The human benchmark (task 4.1)", "", *INTRO["benchmark"],
          f"Each entry was scored by three of the {b['weighted_score']['judges']} judges.", "",
          "| Criterion | Mean | SD | ICC(1) one judge | ICC(1) three | Share of variance: between entries | Judge severity (level noise) | Judge reactions to entries (pattern noise) | One judge vs two |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, v in ordered(b):
        L.append(f"| {NAMES[k]} | {v['mean']:.2f} | {v['sd']:.2f} | {f2(v['icc1_single'])} | {f2(v['icc1_mean'])} | {v['share']['entry']:.0%} | {v['share']['judge']:.0%} | {v['share']['residual']:.0%} | {v['one_judge_vs_other_two']['pearson']:.2f} |")
    L += ["", p.cite("Human benchmark", "human_benchmark", bench), ""]

    # 4.2
    L += ["## 2. Scores (task 4.2, A1)", "", *INTRO["scores"]]
    for judge in ("claude_judge", "qwen_judge"):
        o = agree[judge].outputs
        L += [f"**{JUDGE_NAMES[judge]}**", "",
              "| Criterion | Human mean | AI mean | Difference | r with human mean | Judge vs two | AI vs two | One run vs two | AI minus judge | ICC across runs | Same score in all runs |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, v in ordered(o["by_criterion"]):
            t = v["vs_other_two"]
            L.append(f"| {NAMES[k]} | {v['human_mean']:.2f} | {v['ai_mean']:.2f} | {v['mean_difference']:+.2f} | {v['ai_vs_human_mean']['pearson']:.2f} | {t['one_judge']['pearson']:.2f} | {t['ai_mean_of_runs']['pearson']:.2f} | {t['ai_one_run']['pearson']:.2f} | {ci(t['difference_ai_mean_minus_one_judge'])} | {v['run_consistency']['icc1_single']:.2f} | {v['run_consistency']['share_identical_across_runs']:.0%} |")
        h = o["halo"]
        m = h["multitrait_multimethod"]
        L += ["", f"Halo: the five scores of one evaluation correlate {h['one_evaluation']['human']['mean_correlation']:.2f} on average for a judge and {h['one_evaluation']['ai_one_run']['mean_correlation']:.2f} for one run (first eigenvalue: {h['one_evaluation']['human']['first_eigenvalue_share']:.0%} and {h['one_evaluation']['ai_one_run']['first_eigenvalue_share']:.0%} of the total). Multitrait-multimethod, on entry means: the same criterion across methods correlates {m['same_criterion_across_methods']:.2f}, different criteria across methods {m['different_criteria_across_methods']:.2f}, different criteria within the judges {m['different_criteria_within_human']:.2f} and within the AI {m['different_criteria_within_ai']:.2f}.", "",
              p.cite(f"A1, {JUDGE_NAMES[judge]}", "score_agreement", agree[judge]), ""]

    # 4.3
    L += ["## 3. Rankings, selections and the cutoff (task 4.3, A2 and A3)", "", *INTRO["rankings"]]
    L += ["| | Claude Sonnet 5.5 | Qwen3-8B |", "|---|---|---|"]
    rs = {j: ranks[j].outputs["rankings_and_selection"] for j in ranks}
    L += [f"| Entries ranked | {rs['claude_judge']['entries']} | {rs['qwen_judge']['entries']} |",
          f"| Rank correlation with the judges' mean (Spearman; Kendall) | {rs['claude_judge']['rank_correlation']['spearman']:.2f}; {rs['claude_judge']['rank_correlation']['kendall_tau_b']:.2f} | {rs['qwen_judge']['rank_correlation']['spearman']:.2f}; {rs['qwen_judge']['rank_correlation']['kendall_tau_b']:.2f} |",
          f"| AI selection of {rs['claude_judge']['selected']}: also advanced | {rs['claude_judge']['ai_selection_vs_advanced']['overlap']} | {rs['qwen_judge']['ai_selection_vs_advanced']['overlap']} |",
          f"| AI selection: also in the judges' top {rs['claude_judge']['selected']} | {rs['claude_judge']['ai_selection_vs_human_top']['overlap']} | {rs['qwen_judge']['ai_selection_vs_human_top']['overlap']} |",
          f"| Judges' top {rs['claude_judge']['selected']}: also advanced | {rs['claude_judge']['human_top_vs_advanced']['overlap']} | {rs['qwen_judge']['human_top_vs_advanced']['overlap']} |",
          f"| Would gain under AI selection (advanced: no) | {len(rs['claude_judge']['would_gain'])} | {len(rs['qwen_judge']['would_gain'])} |",
          f"| Would lose under AI selection (advanced: yes) | {len(rs['claude_judge']['would_lose'])} | {len(rs['qwen_judge']['would_lose'])} |",
          f"| Median judges' rank of those who would gain; of those who would lose | {_median(rs['claude_judge']['human_rank_of_those_who_would_gain'])}; {_median(rs['claude_judge']['human_rank_of_those_who_would_lose'])} | {_median(rs['qwen_judge']['human_rank_of_those_who_would_gain'])}; {_median(rs['qwen_judge']['human_rank_of_those_who_would_lose'])} |", "",
          "The codes of those who would gain and lose are in the component's output, for Phase 5 (A5).", "",
          "**The expectations (A3).** Each judge of an entry is held out in turn; the mean of the other two ranks the entries (the reference). In each band of reference positions, the table compares the absolute rank difference of the AI judge's ranking from the reference with the held-out judge's, and the share of entries each ranking places on the other side of the cutoff. Differences are the AI minus the judge, with 95% bootstrap intervals over entries.", ""]
    for judge in ("claude_judge", "qwen_judge"):
        e = ranks[judge].outputs["expectations"]
        L += [f"**{JUDGE_NAMES[judge]}** (bands: strongest, {e['bands']['strongest']}; cutoff, {e['bands']['cutoff']})", "",
              "| Band | Measure | AI | Held-out judge | AI minus judge |", "|---|---|---|---|---|"]
        for band in ("strongest", "cutoff"):
            for key, label in (("mean_absolute_rank_difference", "Rank difference, mean of runs"),
                               ("mean_absolute_rank_difference_one_run", "Rank difference, one run"),
                               ("share_on_the_other_side_of_the_cutoff", "Other side of the cutoff")):
                v = e[band][key]
                L.append(f"| {band} | {label} | {v['ai']:.2f} | {v['judge']:.2f} | {ci(v)} |")
        L += ["", p.cite(f"A2 and A3, {JUDGE_NAMES[judge]}", "ranking_comparison", ranks[judge]), ""]

    # 4.4
    L += ["## 4. Written feedback (task 4.4, A4)", "", *INTRO["feedback"],
          "The three embedders are Qwen3-Embedding-8B, given a task instruction, bge-m3 and gte-modernbert-base, run on Modal at pinned commits. The table pools the five written questions; each row is one embedder.", ""]
    L += ["| Embedder | Specificity: judge–judge | judge–Claude | judge–Qwen | Claude–Claude (runs) | Alike: judges | Alike: Claude | Alike: Qwen | Fit: judges | Fit: Claude | Fit: Qwen |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    signs = {}
    for name in ("embedder_qwen3", "embedder_bge_m3", "embedder_gte_modernbert"):
        o = fb[name].outputs
        si, al, fi = o["same_issues"]["all"], o["alike_across_entries"]["all"], o["fit_to_summary"]["all"]
        row = [si["human~human"]["specificity"], si["human~claude_judge"]["specificity"], si["human~qwen_judge"]["specificity"],
               si["claude_judge~claude_judge"]["specificity"], al["human"], al["claude_judge"], al["qwen_judge"],
               fi["human"]["own_minus_others"], fi["claude_judge"]["own_minus_others"], fi["qwen_judge"]["own_minus_others"]]
        L.append(f"| {name.replace('embedder_', '')} | " + " | ".join(f3(x) for x in row) + " |")
        signs[name] = {"claude_more_alike_than_judges": al["claude_judge"] > al["human"],
                       "claude_fits_better_than_judges": fi["claude_judge"]["own_minus_others"] > fi["human"]["own_minus_others"],
                       "judge_claude_specificity_above_judge_judge": si["human~claude_judge"]["specificity"] > si["human~human"]["specificity"]}
    L += ["", "Holds across all three embedders (design, Section 3: only such findings are reported as findings):", ""]
    for key, label in (("claude_more_alike_than_judges", "Claude's feedback is more alike across entries than the judges'"),
                       ("claude_fits_better_than_judges", "Claude's feedback fits its own summary better than the judges' does"),
                       ("judge_claude_specificity_above_judge_judge", "A judge's comments and Claude's address the entry's issues more specifically than two judges' comments do")):
        values = {n: signs[n][key] for n in signs}
        verdict = "yes" if all(values.values()) else "no" if not any(values.values()) else "mixed"
        L.append(f"- {label}: {'holds for all three' if verdict == 'yes' else 'holds for none' if verdict == 'no' else 'mixed: ' + ', '.join(n.replace('embedder_', '') for n, v in values.items() if v)}.")
    L += ["", "Lengths differ widely (mean words, all questions): " + "; ".join(f"{JUDGE_NAMES.get(s, 'judges')} {fb['embedder_qwen3'].outputs['words']['all'][s]:.0f}" for s in ("human", "claude_judge", "qwen_judge")) + ". The judges' comments are short; the AI judges' outputs are essay-length.", ""]
    for name in ("embedder_qwen3", "embedder_bge_m3", "embedder_gte_modernbert"):
        L.append(p.cite(f"A4 embeddings, {name.replace('embedder_', '')}", "feedback_comparison", fb[name]))
    L.append("")
    L += ["**Do the embedders agree?** Spearman correlations between their pairwise similarities over the same texts (a random sample of the feedback; all summaries).", "",
          "| Pair of embedders | Feedback | Summaries |", "|---|---|---|"]
    fa, sa = fb["agreement:feedback"].outputs["agreement"], fb["agreement:summaries"].outputs["agreement"]
    for pair in fa["spearman"]:
        L.append(f"| {pair.replace('embedder_', '').replace('~', ' and ')} | {fa['spearman'][pair]:.2f} | {sa['spearman'][pair]:.2f} |")
    L += ["", p.cite("Embedders' agreement, feedback", "embedding_agreement", fb["agreement:feedback"]),
          p.cite("Embedders' agreement, summaries", "embedding_agreement", fb["agreement:summaries"]), ""]
    if reexec:
        L += [f"**Re-execution.** The {next(iter(reexec.values()))['texts']} summaries embedded again in a new container gave " + "; ".join(
            f"{n.replace('embedder_', '')}: {'bit-identical vectors' if v['identical'] else 'different vectors'}" for n, v in reexec.items()) + ".", ""]

    t = fb["text"].outputs
    L += ["**Text analysis.** Mean words, hedges per 100 words (Hyland 2005), and tone (VADER compound score, from −1 to 1; Hutto & Gilbert 2014), by question.", "",
          "| Question | Words: judges | Claude | Qwen | Hedges: judges | Claude | Qwen | Tone: judges | Claude | Qwen |", "|---|---|---|---|---|---|---|---|---|---|"]
    m = t["measures"]
    for q, label in QUESTIONS.items():
        L.append(f"| {label} | {m['human'][q]['mean_words']:.0f} | {m['claude_judge'][q]['mean_words']:.0f} | {m['qwen_judge'][q]['mean_words']:.0f} | "
                 f"{m['human'][q]['hedges_per_100_words']:.1f} | {m['claude_judge'][q]['hedges_per_100_words']:.1f} | {m['qwen_judge'][q]['hedges_per_100_words']:.1f} | "
                 f"{m['human'][q]['tone']:.2f} | {m['claude_judge'][q]['tone']:.2f} | {m['qwen_judge'][q]['tone']:.2f} |")
    L += ["", "Words most typical of the judges' feedback and of Claude's, by question (log-odds with an informative Dirichlet prior; Monroe, Colaresi & Quinn 2008). A word must appear in feedback on at least five entries and cannot be a name.", "",
          "| Question | Judges | Claude |", "|---|---|---|"]
    for q, label in QUESTIONS.items():
        d = t["distinguishing_words"][q]["claude_judge"]
        L.append(f"| {label} | {', '.join(w['word'] for w in d['human'][:10])} | {', '.join(w['word'] for w in d['ai'][:10])} |")
    L += ["", p.cite("A4 text analysis", "feedback_text", fb["text"]), ""]

    if expl:
        L += _phase5_sections(p, meas, expl, rs=ranks, agree=agree)
    caveat_number = 9 if expl else 5
    L += [f"## {caveat_number}. Caveats" + (" and future work" if expl else ""), "",
          f"- One year: {summaries} judged summaries. The findings are exploratory until further years test them.",
          "- The AI judge's score is the mean of five runs, which is more reliable than a single judge's score; the score of one run is reported beside it and yields nearly the same results.",
          ("- In the synthetic competition, the judges' top 30% by mean weighted score advance; the judges' own top and those who advanced therefore coincide."
           if synthetic() else
           "- Advancement follows the judges' ranking but skips entries that missed a requirement of the process, such as legally forming the business (organizers); A2 therefore compares the selection by AI scores both with those who advanced and with the judges' own top."),
          "- The AI judges' written answers are many times longer than the judges' comments. The embedding measures are built to be robust to length, but the embedders have no validation against human similarity ratings." + (" Their similarities track the teams' own categories (Section 5)." if expl else " Phase 5 checks them."),
          "- The text measures (hedging, tone) are dictionary counts, not validated for this genre." + ("" if expl else " Phase 5's profiler replaces them."),
          ("- The synthetic summaries are plain PDF and Word files, and their texts are therefore extracted cleanly. The layouts of real summaries, which can disorder the extracted text, are not reproduced."
           if synthetic() else
           "- The authors' visual check of 20 extractions found every text complete, but the reading order wrong in 4 (a slide deck, mixed or two-column layouts with images, pages in reverse order), all among the summaries that agreed least with the earlier extraction. For such summaries the AI judges received text in the wrong order, whereas the human judges saw the layout.")]
    if expl:
        L += ["- No human coders were available. Novelty and topics are therefore described, not tested, and the framework's methodological check keeps them out of inference. The embedding similarities were checked against the teams' own categories instead.",
              f"- The A5 models test many coefficients on {summaries} entries; they are to be read as patterns to be tested on further years, not as findings.",
              "", "**Future work.**",
              "- Validate novelty and the similarities against two coders' ratings, with the protocol and thresholds of the plan's Section 3 (Later: human validation of the measures); then add novelty to A5's regressions with a bias correction.",
              "- A6: change over the editions since 2019, including a break after ChatGPT's release in late 2022.",
              "- Further years, to test the findings of Section 8 (Study B, B5).",
              "- An outside researcher's reproduction of a headline result from the package alone (B4)."]
    L.append("")
    store = data_dir() / "store" / "provenance"
    store = store.relative_to(ROOT) if store.is_relative_to(ROOT) else store
    L += ["## Provenance", "", f"Every number above comes from a stored component output with a provenance record in `{store}/`.", ""]
    L += p.table()
    return "\n".join(L) + "\n"


def _summary(b: dict, agree: dict, ranks: dict, fb: dict, meas: dict | None, expl: dict | None) -> list[str]:
    """The summary, in plain words: what was measured, what the numbers mean, and what was found.
    Statements that depend on the results are checked against them."""
    w = b["weighted_score"]
    c, q = agree["claude_judge"].outputs, agree["qwen_judge"].outputs
    cw, qw = c["by_criterion"]["weighted_score"], q["by_criterion"]["weighted_score"]
    criteria = [v for k, v in c["by_criterion"].items() if k != "weighted_score"]
    better = sum(v["vs_other_two"]["difference_ai_mean_minus_one_judge"]["low"] > 0 for v in criteria)
    halo_h = c["halo"]["one_evaluation"]["human"]["mean_correlation"]
    halo_c = c["halo"]["one_evaluation"]["ai_one_run"]["mean_correlation"]
    sel = ranks["claude_judge"].outputs["rankings_and_selection"]
    exp = ranks["claude_judge"].outputs["expectations"]
    top, cut = exp["strongest"]["mean_absolute_rank_difference"], exp["cutoff"]["mean_absolute_rank_difference"]
    flip = exp["cutoff"]["share_on_the_other_side_of_the_cutoff"]
    strict = lambda d: f"{abs(d):.2f} points {'lower' if d < 0 else 'higher'}"
    out = [
        f"- **The human judges agree {'only weakly' if w['reliability_mean_of_3'] < 0.7 else 'fairly well'} with one another.** The judges' weighted scores differ from one evaluation to the next, and a statistical model splits those differences into three sources. Only {w['share']['entry']:.0%} reflect real differences between the summaries, the signal the scores are meant to capture. The remaining variance divides into {w['share']['judge']:.0%} from some judges scoring every summary higher or lower than others do (*level noise*) and {w['share']['residual']:.0%} from judges reacting differently to the same summary (*pattern noise*). The average of an entry's three judges therefore has a reliability of {w['reliability_mean_of_3']:.2f}: if three other judges, chosen the same way, scored the same summaries, their averages would correlate {'only ' if w['reliability_mean_of_3'] < 0.7 else ''}about {w['reliability_mean_of_3']:.2f} with the actual ones. One judge's score correlates {w['one_judge_vs_other_two']['pearson']:.2f} with the average of the entry's other two judges.",
        f"- **{_versus_judge(cw)}** Each AI judge was compared with the average of two of an entry's judges, exactly as the third judge is. On the {cw['entries']} summaries with AI evaluations, Claude's weighted score (the average of its five runs) correlates {cw['vs_other_two']['ai_mean_of_runs']['pearson']:.2f} with the two judges' average, a single Claude run {cw['vs_other_two']['ai_one_run']['pearson']:.2f}, and the third judge {cw['vs_other_two']['one_judge']['pearson']:.2f}. "
        + (f"Claude's scores agree more closely on every criterion. " if better == len(criteria) else f"Claude's scores agree clearly more closely on {better} of the {len(criteria)} criteria. ")
        + f"The scores of Qwen3-8B, the open-weight AI judge used as a check, {_qwen_versus(cw, qw)} ({qw['vs_other_two']['ai_mean_of_runs']['pearson']:.2f}).",
        f"- **Claude's scores are {'lower' if cw['mean_difference'] < 0 else 'higher'} than the judges', and Qwen3-8B's {'lower' if qw['mean_difference'] < 0 else 'higher'}:** on the 1-to-10 weighted score, Claude's average is {strict(cw['mean_difference'])} than the judges', and Qwen3-8B's {strict(qw['mean_difference'])}. "
        + ("**The scores of both are highly consistent across runs:** posed the same question again, each returns nearly the same score." if min(cw['run_consistency']['icc1_single'], qw['run_consistency']['icc1_single']) >= 0.9 else "**The consistency of their scores across runs:**")
        + f" The consistency of their scores across the five runs, measured by the intraclass correlation (ICC: the share of the variation in their scores that reflects differences between summaries rather than between runs, where 1 means identical runs), is {cw['run_consistency']['icc1_single']:.2f} for Claude and {qw['run_consistency']['icc1_single']:.2f} for Qwen3-8B.",
        f"- **Halo is " + ("stronger in the human judges' scores" if halo_h > halo_c else "stronger in Claude's scores") + f".** Halo is the tendency of one overall impression to colour every criterion. A judge's five scores of a summary correlate {halo_h:.2f} with one another on average; one Claude run's five scores, {halo_c:.2f}. " + ("Claude's scores distinguish the criteria more than the judges' do." if halo_c < halo_h else ""),
        f"- **The selections overlap partly.** If the {sel['selected']} entries with Claude's highest scores were selected, {sel['ai_selection_vs_advanced']['overlap']} of them would be among the {sel['selected']} that advanced. The judges' own top {sel['selected']} includes {sel['human_top_vs_advanced']['overlap']} of those who advanced" + ("; the others were skipped for missing a requirement of the process." if sel['human_top_vs_advanced']['overlap'] < sel['selected'] and not synthetic() else "."),
        "- **The design's two expectations.** "
        + ("As expected, among the strongest entries Claude's ranks differ from the judges' no more than the judges' ranks differ among themselves. " if top["difference"] <= 0 or top["low"] <= 0 else "Contrary to expectation, among the strongest entries Claude's ranks differ from the judges' more than the judges' ranks differ among themselves. ")
        + ("Contrary to expectation, near the cutoff for advancing Claude's ranks do not diverge from the judges' more than a third judge's would: they are closer to the two judges' than a third judge's are" if cut["high"] < 0 else "Near the cutoff, Claude's ranks differ from the two judges' about as much as a third judge's do" if cut["low"] <= 0 else "As expected, near the cutoff Claude's ranks diverge from the judges' more than a third judge's do")
        + (", and Claude's ranking places entries on the other side of the cutoff about as often as a third judge's does." if flip["low"] <= 0 <= flip["high"] else "."),
        _feedback_summary(fb),
    ]
    if expl:
        out += _phase5_summary(meas, expl)
    return out


def _versus_judge(cw: dict) -> str:
    """The headline on agreement: from the interval of Claude's correlation minus the third judge's."""
    d = cw["vs_other_two"]["difference_ai_mean_minus_one_judge"]
    how = "more closely than" if d["low"] > 0 else "less closely than" if d["high"] < 0 else "about as closely as"
    return f"The AI judges' scores agree with the human judges' {how} one more human judge's do."


def _qwen_versus(cw: dict, qw: dict) -> str:
    third = qw["vs_other_two"]["one_judge"]["pearson"]
    q, c = qw["vs_other_two"]["ai_mean_of_runs"]["pearson"], cw["vs_other_two"]["ai_mean_of_runs"]["pearson"]
    claude_closer = cw["vs_other_two"]["ai_mean_of_runs"]["pearson"] > cw["vs_other_two"]["one_judge"]["pearson"]
    text = ("also " if claude_closer and q > third else "") + ("agree more closely than the third judge's" if q > third else "agree less closely than the third judge's")
    return text + (", but less closely than Claude's" if q < c else ", and more closely than Claude's")


def _feedback_summary(fb: dict) -> str:
    rows = {n: fb[n].outputs for n in ("embedder_qwen3", "embedder_bge_m3", "embedder_gte_modernbert")}
    first = {n: (o["fit_to_summary"]["all"]["claude_judge"]["own_ranked_first"], o["fit_to_summary"]["all"]["human"]["own_ranked_first"])
             for n, o in rows.items()}
    words = rows["embedder_qwen3"]["words"]["all"]
    n_summaries = rows["embedder_qwen3"]["entries"]
    c_lo, c_hi = min(v[0] for v in first.values()), max(v[0] for v in first.values())
    h_lo, h_hi = min(v[1] for v in first.values()), max(v[1] for v in first.values())
    al = {n: o["alike_across_entries"]["all"] for n, o in rows.items()}
    si = {n: o["same_issues"]["all"] for n, o in rows.items()}
    alike = all(a["claude_judge"] > a["human"] for a in al.values())
    specific = all(x["human~claude_judge"]["specificity"] > x["human~human"]["specificity"] for x in si.values())
    clauses = ["Claude's comments discuss each entry's own issues " + ("more than" if specific else "no more than") + " the judges' comments do"]
    clauses += ["they are " + ("more" if alike else "no more") + " alike from one entry to the next"]
    clauses += ["they are tied far more closely to the summary they concern" if c_lo > h_hi
                else "they are tied to the summary they concern about as closely as the judges' comments are"]
    measures = fb["text"].outputs["measures"]
    mean = lambda source, key: sum(v[key] for v in measures[source].values()) / len(measures[source])
    hedges = "fewer" if mean("claude_judge", "hedges_per_100_words") < mean("human", "hedges_per_100_words") else "more"
    tone_gap = mean("qwen_judge", "tone") - mean("human", "tone")
    tone = ("a markedly more positive tone" if tone_gap >= 0.2 else "a more positive tone" if tone_gap > 0 else "a less positive tone")
    return (f"- **The AI judges' written feedback differs from the judges'.** The AI judges' outputs are essays, whereas the judges' comments are short: "
            f"{words['claude_judge']:.0f} words on average for Claude, {words['human']:.0f} for a judge. To compare the content of the texts, three different "
            f"*embedding models* (AI models that turn a text into a list of numbers representing its meaning; using three guards against the idiosyncrasies of any one) "
            f"converted every text into numbers, and texts were compared by how similar their numbers are. With all three models, "
            + ("; ".join(clauses[:-1]) + "; and " if len(clauses) > 1 else "") + clauses[-1]
            + f". For the last of these, each comment was compared with all {n_summaries} summaries: "
            f"the summary it resembled most was its own for {c_lo:.0%} to {c_hi:.0%} of Claude's outputs, depending on the model, and for {h_lo:.0%} to {h_hi:.0%} "
            f"of the judges' comments, where chance alone would give under {1 / n_summaries:.0%}. Claude's comments also contain {hedges} hedges than the judges', and Qwen3-8B's have {tone}. "
            f"The words most typical of Claude's feedback are {', '.join(_common_words(fb['text'].outputs, 'claude_judge', 'ai'))}; "
            f"of the judges', {', '.join(_common_words(fb['text'].outputs, 'claude_judge', 'human'))}.")


def _common_words(text: dict, judge: str, side: str, n: int = 6) -> list[str]:
    """The words that appear in the most questions' lists of distinctive words, ties by mean z."""
    from collections import defaultdict
    seen = defaultdict(list)
    for q in text["distinguishing_words"].values():
        for w in q[judge][side][:10]:
            seen[w["word"]].append(abs(w["z"]))
    return sorted(seen, key=lambda w: (-len(seen[w]), -sum(seen[w]) / len(seen[w])))[:n]


def _phase5_summary(meas: dict, expl: dict) -> list[str]:
    x = expl["explanation"].outputs
    e = x["explained"]
    kg = meas["known_groups"].outputs["by_embedder"]
    d_lo, d_hi = min(v["standardized_difference"] for v in kg.values()), max(v["standardized_difference"] for v in kg.values())
    rel = meas["novelty"].outputs["agreement"]
    gaps = x["intervals"]["claude_minus_human"]
    chance = all(gaps[g]["low"] <= 0 <= gaps[g]["high"] for g in ("form", "substance"))
    n_features = len(x["coefficients"]["human"])
    longer = all(x["coefficients"][k]["log_words"]["low"] > 0 for k in ("human", "claude"))
    gap = {k: e[k]["form"] - e[k]["substance"] for k in ("human", "claude")}
    each = {k: "about as much as" if abs(g) <= 0.1 else "more than" if g > 0 else "less than" for k, g in gap.items()}
    headline = (f"how a summary is written matters {each['human']} what the venture is, for the judges' scores and for Claude's"
                if each["human"] == each["claude"] else
                f"how a summary is written matters {each['human']} what the venture is for the judges' scores, but "
                f"{each['claude'].replace(' than', '').replace(' as much as', ' as much')} for Claude's")
    hard = e["divergence_claude"]["adjusted_both"] < 0.1
    agree_n = rel["mean_spearman_between_embedders"]
    gap_words = ("are clearly more similar under all three models than pairs with nothing in common, by {lo:.2f} to {hi:.2f} standard deviations, a large gap"
                 if d_lo >= 0.8 else
                 "are more similar under all three models than pairs with nothing in common, by {lo:.2f} to {hi:.2f} standard deviations, a moderate gap"
                 if d_lo >= 0.5 else
                 "are only slightly more similar under the three models than pairs with nothing in common, by {lo:.2f} to {hi:.2f} standard deviations"
                 if d_lo > 0 else
                 "are not consistently more similar under the three models than pairs with nothing in common ({lo:.2f} to {hi:.2f} standard deviations)").format(lo=d_lo, hi=d_hi)
    return [
        f"- **What goes with higher scores: {headline}.** "
        f"We asked how much of the differences in scores between summaries two groups of features can predict: the summary's *form* (its length, readability, "
        f"hedging, confident wording, numbers, and the team writing as \"we\") and the venture's *substance* (its type of product, milestones reached, legal entity "
        f"and website). Form predicts {e['human']['form']:.0%} of the differences in the judges' scores and {e['claude']['form']:.0%} in Claude's; substance "
        f"predicts {e['human']['substance']:.0%} and {e['claude']['substance']:.0%}. "
        + ("The gaps between the judges' scores and Claude's are within what chance alone would produce; neither set of scores therefore depends clearly more on form than the other. " if chance else "")
        + ("Longer summaries receive higher scores from both." if longer else ""),
        f"- **Where Claude's scores and the judges' disagree is {'hard to predict' if hard else 'partly predictable'}.** All {n_features} features together predict {e['divergence_claude']['both']:.0%} of the "
        f"differences between Claude's scores and the judges', and only {max(e['divergence_claude']['adjusted_both'], 0):.0%} after allowing for the prediction that "
        f"{n_features} features would produce by chance alone (the *adjusted* figure)." + ((" The clear pattern: " + clause + ".") if (clause := _divergence_clause(x["coefficients"]["divergence_claude"])) else " No single feature stands out."),
        _advancement_text(x["advancement"]),
        f"- **Novelty and topics can only be described.** Novelty (how different a summary is from the year's other summaries) was measured with each of "
        f"the three embedding models. Their scores agree {'only moderately' if agree_n < 0.6 else 'well'} and are therefore averaged; the average has a reliability of {rel['spearman_brown_reliability']:.2f} "
        f"(on the same 0-to-1 scale as above). To check that the models' similarity measures are meaningful without human coders, we used the teams' own choices of "
        f"fields on the application form: pairs of ventures that chose the same fields {gap_words}. Without human ratings of novelty, the framework keeps "
        f"novelty out of statistical tests; novelty is therefore only described.",
    ]


def _phase5_sections(p, meas: dict, expl: dict, rs: dict, agree: dict) -> list[str]:
    import pandas as pd

    st = pd.DataFrame(meas["style"].outputs["profile"])
    L = ["## 5. Measures (tasks 5.1 and 5.2)", "", *INTRO["measures"],
         f"**Style and language profile** of the {len(st)} summaries (code only, no model).", "",
         "| Measure | Mean | SD | Min | Max |", "|---|---|---|---|---|"]
    for col, label in (("words", "Words"), ("flesch_reading_ease", "Flesch reading ease"), ("flesch_kincaid_grade", "Flesch-Kincaid grade"),
                       ("hedges_per_100_words", "Hedges per 100 words"), ("boosters_per_100_words", "Boosters per 100 words"),
                       ("numbers_per_100_words", "Numbers per 100 words"), ("we_per_100_words", "We, our, us per 100 words")):
        v = st[col]
        L.append(f"| {label} | {v.mean():.1f} | {v.std():.1f} | {v.min():.1f} | {v.max():.1f} |")
    over = st["over_page_limit"].dropna()
    L += ["", f"{int(over.sum())} of {len(over)} PDFs exceed the two-page limit.", "",
          p.cite("Style profile", "style_profiler", meas["style"]), ""]
    rel = meas["novelty"].outputs["agreement"]
    L += ["**Novelty** is each summary's distance from its five most similar summaries of the year; the composite averages the three embedders' standardized scores. "
          f"The embedders' novelty scores agree with a mean Spearman correlation of {rel['mean_spearman_between_embedders']:.2f}; the composite's reliability is accordingly {rel['spearman_brown_reliability']:.2f}. "
          "No human ratings of novelty exist in this study; novelty is therefore described, not tested.", "",
          p.cite("Novelty composite", "novelty_composite", meas["novelty"]), "",
          "**Similarity, checked against the teams' own categories.** Pairs of judged summaries whose teams chose at least two of the same fields, against pairs with no field and no type of product in common; the threshold, set before the check, was a 95% interval excluding zero.", "",
          "| Embedder | Pairs (same; nothing in common) | Mean similarity (same; nothing) | Difference | Standardized | Correlation with category overlap | Passed |",
          "|---|---|---|---|---|---|---|"]
    for name, v in meas["known_groups"].outputs["by_embedder"].items():
        L.append(f"| {name.replace('embedder_', '')} | {v['pairs_same_fields']}; {v['pairs_nothing_in_common']} | {v['mean_similarity_same_fields']:.3f}; {v['mean_similarity_nothing_in_common']:.3f} | "
                 f"{v['difference']:+.3f} [{v['low']:+.3f}, {v['high']:+.3f}] | {v['standardized_difference']:.2f} | {v['spearman_with_category_overlap']:.2f} | {'yes' if v['passed'] else 'no'} |")
    L += ["", p.cite("Similarity, known groups", "similarity_known_groups", meas["known_groups"]), ""]
    ta = meas["topic_agreement"].outputs["adjusted_rand"]
    L += ["**Topics.** Ward clusters of each embedder's whitened vectors, the number chosen by the silhouette: " + "; ".join(
          f"{n.replace('embedder_', '')} {meas[f'topics:{n}'].outputs['topics']} topics (silhouette {meas[f'topics:{n}'].outputs['silhouette'][str(meas[f'topics:{n}'].outputs['topics'])]:.2f})"
          for n in ("embedder_qwen3", "embedder_bge_m3", "embedder_gte_modernbert")) + ". The embedders' topics agree only modestly (adjusted Rand index " +
          ", ".join(f"{v:.2f}" for v in ta.values()) + "); topics are therefore descriptive. The topics of Qwen3-Embedding, by their most distinctive words:", "",
          "| Topic | Summaries | Distinctive words |", "|---|---|---|"]
    tq = meas["topics:embedder_qwen3"].outputs
    for k, words in sorted(tq["words"].items(), key=lambda kv: int(kv[0])):
        L.append(f"| {k} | {tq['sizes'][k]} | {', '.join(words[:8])} |")
    L += ["", p.cite("Topics, Qwen3-Embedding", "topics", meas["topics:embedder_qwen3"]),
          p.cite("Topic agreement", "topic_agreement", meas["topic_agreement"]), ""]

    x = expl["explanation"].outputs
    L += ["## 6. What explains the scores (task 5.3, A5)", "", *INTRO["explain"],
          f"{x['entries']} judged entries; scores are standardized.", "",
          "| Outcome | Form | Substance | Both | Both, adjusted | Form minus substance |", "|---|---|---|---|---|---|"]
    labels = {"human": "Judges", "claude": "Claude Sonnet 5.5", "qwen": "Qwen3-8B", "divergence_claude": "Divergence, Claude", "divergence_qwen": "Divergence, Qwen3-8B"}
    for k, label in labels.items():
        v, i = x["explained"][k], x["intervals"]["form_minus_substance"][k]
        L.append(f"| {label} | {v['form']:.2f} | {v['substance']:.2f} | {v['both']:.2f} | {v['adjusted_both']:.2f} | [{i['low']:+.2f}, {i['high']:+.2f}] |")
    ch = x["intervals"]["claude_minus_human"]
    L += ["", "Claude minus the judges, in variance explained (95% intervals): " + "; ".join(f"{g} [{v['low']:+.2f}, {v['high']:+.2f}]" for g, v in ch.items()) + ".", "",
          "Coefficients in the model with both groups (standardized outcome; continuous features standardized, binary ones 0 or 1), with 95% intervals (HC3). In bold, intervals that exclude zero.", "",
          "| Feature | Judges | Claude | Divergence |", "|---|---|---|---|"]
    from ..runner import Component

    settings = Component("score_explanation").settings
    for f in settings["form"] + settings["substance"]:
        cells = []
        for k in ("human", "claude", "divergence_claude"):
            v = x["coefficients"][k][f]
            text = f"{v['coefficient']:+.2f} [{v['low']:+.2f}, {v['high']:+.2f}]"
            cells.append(f"**{text}**" if v["low"] > 0 or v["high"] < 0 else text)
        L.append(f"| {f.replace('_', ' ')} | " + " | ".join(cells) + " |")
    a = x["advancement"]
    hs = a["linear_probability"]["human_score"]
    L += ["", f"**Who advanced** ({a['advanced']} of {x['entries']}). In a linear probability model with the judges' score and every feature, one standard deviation of the judges' score raises the probability of advancing by {hs['coefficient']:.2f} [{hs['low']:.2f}, {hs['high']:.2f}]; "
          + ("no feature's interval excludes zero." if not any((v['low'] > 0 or v['high'] < 0) for c, v in a['linear_probability'].items() if c != 'human_score') else "the features whose intervals exclude zero: " + ", ".join(c for c, v in a['linear_probability'].items() if c != 'human_score' and (v['low'] > 0 or v['high'] < 0)) + ".")
          + " Added to the judges' score, " + "; ".join(f"{JUDGE_NAMES[j + '_judge']}'s score changes it by {d[j + '_score']['coefficient']:+.2f} [{d[j + '_score']['low']:+.2f}, {d[j + '_score']['high']:+.2f}]" for j, d in a['ai_score_beyond_human_score'].items()) + ".", "",
          p.cite("A5", "score_explanation", expl["explanation"]), "",
          "**Novelty and the scores: a description, not a test.** Mean weighted scores and the share advanced in each fifth of the entries by the novelty composite.", "",
          "| Fifth by novelty | Entries | Judges | Claude | Qwen3-8B | Advanced |", "|---|---|---|---|---|---|"]
    for b in expl["novelty"].outputs["by_bin"]:
        L.append(f"| {b['bin']} | {b['entries']} | {b['human']:.2f} | {b['claude']:.2f} | {b['qwen']:.2f} | {b['share_advanced']:.0%} |")
    L += ["", p.cite("Novelty profile", "novelty_profile", expl["novelty"]), ""]

    L += ["## 7. Change over the years (A6)", "",
          ("The synthetic competition has one edition. In the project, A6 studies how human and AI evaluations change over the editions since 2019 (plan, task 7.3)."
           if synthetic() else
           "The finalists and winners cannot be obtained; A6 therefore studies how human and AI evaluations change over the editions since 2019, beginning with the second edition (plan, task 7.3)."), ""]
    L += _hypotheses(agree, rs, x)
    return L


def _hypotheses(agree: dict, ranks: dict, x: dict) -> list[str]:
    """Task 5.5: the findings of 2019 to test on further years, each with its 2019 estimate."""
    c = agree["claude_judge"].outputs
    w = c["by_criterion"]["weighted_score"]
    d = w["vs_other_two"]["difference_ai_mean_minus_one_judge"]
    halo = c["halo"]["one_evaluation"]
    e = ranks["claude_judge"].outputs["expectations"]
    cut, top = e["cutoff"]["mean_absolute_rank_difference"], e["strongest"]["mean_absolute_rank_difference"]
    coef = x["coefficients"]
    read = coef["divergence_claude"]["flesch_reading_ease"]
    words_h, words_c = coef["human"]["log_words"], coef["claude"]["log_words"]
    beyond = x["advancement"]["ai_score_beyond_human_score"]["claude"]["claude_score"]
    return ["## 8. Findings to test on further years (task 5.5)", "",
            ("These are the findings of the 2019 records. The estimates that follow each are the synthetic competition's, whose judges are simulated; they therefore show the components at work and confirm or refute nothing."
             if synthetic() else
             "Each is stated in a form that a further year can confirm or refute with the same components; this year's estimate follows."), "",
            f"1. **An AI judge's scores agree with the panel's more closely than one more human judge's do.** Against the mean of two judges, the AI judge's weighted score (mean of five runs) correlates more highly than the third judge's. This year, Claude: {w['vs_other_two']['ai_mean_of_runs']['pearson']:.2f} against {w['vs_other_two']['one_judge']['pearson']:.2f}; difference {d['estimate']:+.2f} [{d['low']:+.2f}, {d['high']:+.2f}].",
            f"2. **Claude's scores are lower than the judges'.** This year: {w['mean_difference']:+.2f} points on the weighted score.",
            f"3. **Halo is stronger in the human judges' scores than in Claude's.** This year: the five scores of one evaluation correlate {halo['human']['mean_correlation']:.2f} for a judge and {halo['ai_one_run']['mean_correlation']:.2f} for a Claude run.",
            f"4. **The ranks of AI and human judges agree on the strongest entries at least as well as the judges' ranks agree among themselves.** This year, rank difference among the ten strongest: Claude {top['ai']:.1f}, third judge {top['judge']:.1f}; difference {top['difference']:+.1f} [{top['low']:+.1f}, {top['high']:+.1f}].",
            f"5. **Near the advancement cutoff, an AI judge's ranks do not diverge from the judges' more than a third judge's do**, contrary to the design's expectation. This year: Claude's ranks {cut['ai']:.1f} places from the reference, the third judge's {cut['judge']:.1f}; difference {cut['difference']:+.1f} [{cut['low']:+.1f}, {cut['high']:+.1f}].",
            "6. **AI feedback is more specific to its entry, more alike across entries and more tied to its own summary than judges' feedback**, under every embedder (Section 4).",
            f"7. **Longer summaries receive higher scores from both the judges and Claude.** This year, per standard deviation of log length: judges {words_h['coefficient']:+.2f} [{words_h['low']:+.2f}, {words_h['high']:+.2f}], Claude {words_c['coefficient']:+.2f} [{words_c['low']:+.2f}, {words_c['high']:+.2f}].",
            f"8. **Denser, harder-to-read summaries receive relatively higher scores from Claude than from the judges.** This year, divergence per standard deviation of reading ease: {read['coefficient']:+.2f} [{read['low']:+.2f}, {read['high']:+.2f}].",
            f"9. **Advancement follows the judges' score, and AI scores add nothing to it.** This year, Claude's score added to the judges': {beyond['coefficient']:+.2f} [{beyond['low']:+.2f}, {beyond['high']:+.2f}].",
            "10. **Novelty and scores** (once novelty is validated against human ratings): whether the inverted U of optimal distinctiveness appears. This year shows no clear pattern, by description only.", ""]


DIRECTIONS = {"flesch_reading_ease": ("easier to read", "denser, harder-to-read"), "log_words": ("longer", "shorter"),
              "hedges_per_100_words": ("more hedged", "less hedged"), "boosters_per_100_words": ("more assertive", "less assertive"),
              "numbers_per_100_words": ("more quantified", "less quantified"), "we_per_100_words": ("more first-person", "less first-person"),
              "milestones_reached": ("further along", "less far along")}


def _feature_phrase(feature: str, coefficient: float) -> str:
    if feature in DIRECTIONS:
        return f"{DIRECTIONS[feature][0 if coefficient > 0 else 1]} summaries"
    return f"entries {'with' if coefficient > 0 else 'without'} {feature.replace('_', ' ')}"


def _divergence_clause(coefficients: dict) -> str | None:
    """The features whose intervals exclude zero, as the summaries that receive relatively higher scores from Claude."""
    clear = {f: v for f, v in coefficients.items() if v["low"] > 0 or v["high"] < 0}
    if not clear:
        return None
    phrases = " and ".join(_feature_phrase(f, v["coefficient"]) for f, v in clear.items())
    return phrases + " receive relatively higher scores from Claude than from the judges"


def _advancement_text(a: dict) -> str:
    features = [f for f, v in a["linear_probability"].items() if f != "human_score" and (v["low"] > 0 or v["high"] < 0)]
    ai_adds = [j for j, d in a["ai_score_beyond_human_score"].items() if d[f"{j}_score"]["low"] > 0 or d[f"{j}_score"]["high"] < 0]
    text = "- **Who advanced.** Advancement follows the judges' scores. "
    text += ("The scores of " + " and ".join(JUDGE_NAMES[j + "_judge"] for j in ai_adds) + " add to predicting it" if ai_adds else "Neither AI judge's scores add to predicting it")
    text += (", and of the summaries' and ventures' features only " + ", ".join(f.replace("_", " ") for f in features) + " do." if features
             else ", and neither does any feature of the summary or the venture.")
    return text


def _median(values):
    import statistics
    return f"{statistics.median(values):.0f}" if values else "–"
