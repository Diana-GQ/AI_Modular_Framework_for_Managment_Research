# Study A: the synthetic competition (fictional year 2000)

Written 2026-10-24 from the components' stored outputs (plan, Phases 4 and 5). Exploratory: the analyses of 2000 suggest findings that further years test (design, Section 7). Counts and statistics only.

**Synthetic data.** This report is on the synthetic competition that the public package carries (design, B4): invented ventures, summaries, judges, scores and comments, generated as `synthetic/README.md` describes. The judges' scores are simulated with the shares of variance and the halo measured on the 2019 judges as targets; with 40 ventures and 15 judges, the shares realized here differ from them by chance (Section 1). The AI judges are the real ones. The numbers show the pipeline at work and test nothing about real judges.

## About this report

Study A compares the evaluations of the same executive summaries by the competition's human judges and by two AI judges, to identify where and why the evaluations agree and differ. Three human judges scored each summary from 1 to 10 on five criteria (concept, business model, market, written work, investor interest) and wrote comments. The same questions were posed five times to each AI judge, Claude Sonnet 5.5 and the open-weight Qwen3-8B; each time is a *run*. Claude is the main AI judge; Qwen3-8B is a check that can be re-executed exactly.

Terms used throughout:
- *Weighted score*: the competition's overall score of one evaluation, 0.2 × concept + 0.2 × business model + 0.2 × market + 0.1 × written work + 0.3 × investor interest.
- *Correlation* (Pearson's r): how closely two sets of numbers rise and fall together, from −1 to 1, where 0 means no relation. *Spearman's correlation* does the same with ranks.
- *95% interval*: the range of values compatible with the data, from re-running the calculation on 2,000 resamples of the entries (a bootstrap). If it excludes zero, the difference is unlikely to be chance.
- *Standardized*: expressed in standard deviations, which allows measures on different scales to be compared.

## Summary

- **The human judges agree only weakly with one another.** The judges' weighted scores differ from one evaluation to the next, and a statistical model splits those differences into three sources. Only 14% reflect real differences between the summaries, the signal the scores are meant to capture. The remaining variance divides into 38% from some judges scoring every summary higher or lower than others do (*level noise*) and 48% from judges reacting differently to the same summary (*pattern noise*). The average of an entry's three judges therefore has a reliability of 0.33: if three other judges, chosen the same way, scored the same summaries, their averages would correlate only about 0.33 with the actual ones. One judge's score correlates 0.13 with the average of the entry's other two judges.
- **The AI judges' scores agree with the human judges' more closely than one more human judge's do.** Each AI judge was compared with the average of two of an entry's judges, exactly as the third judge is. On the 40 summaries with AI evaluations, Claude's weighted score (the average of its five runs) correlates 0.44 with the two judges' average, a single Claude run 0.45, and the third judge 0.13. Claude's scores agree clearly more closely on 2 of the 5 criteria. The scores of Qwen3-8B, the open-weight AI judge used as a check, also agree more closely than the third judge's, but less closely than Claude's (0.33).
- **Claude's scores are lower than the judges', and Qwen3-8B's higher:** on the 1-to-10 weighted score, Claude's average is 0.94 points lower than the judges', and Qwen3-8B's 1.79 points higher. **The scores of both are highly consistent across runs:** posed the same question again, each returns nearly the same score. The consistency of their scores across the five runs, measured by the intraclass correlation (ICC: the share of the variation in their scores that reflects differences between summaries rather than between runs, where 1 means identical runs), is 0.99 for Claude and 0.94 for Qwen3-8B.
- **Halo is stronger in the human judges' scores.** Halo is the tendency of one overall impression to colour every criterion. A judge's five scores of a summary correlate 0.70 with one another on average; one Claude run's five scores, 0.60. Claude's scores distinguish the criteria more than the judges' do.
- **The selections overlap partly.** If the 12 entries with Claude's highest scores were selected, 6 of them would be among the 12 that advanced. The judges' own top 12 includes 12 of those who advanced.
- **The design's two expectations.** As expected, among the strongest entries Claude's ranks differ from the judges' no more than the judges' ranks differ among themselves. Contrary to expectation, near the cutoff for advancing Claude's ranks do not diverge from the judges' more than a third judge's would: they are closer to the two judges' than a third judge's are, and Claude's ranking places entries on the other side of the cutoff about as often as a third judge's does.
- **The AI judges' written feedback differs from the judges'.** The AI judges' outputs are essays, whereas the judges' comments are short: 592 words on average for Claude, 50 for a judge. To compare the content of the texts, three different *embedding models* (AI models that turn a text into a list of numbers representing its meaning; using three guards against the idiosyncrasies of any one) converted every text into numbers, and texts were compared by how similar their numbers are. With all three models, Claude's comments discuss each entry's own issues no more than the judges' comments do; they are more alike from one entry to the next; and they are tied far more closely to the summary they concern. For the last of these, each comment was compared with all 40 summaries: the summary it resembled most was its own for 98% to 100% of Claude's outputs, depending on the model, and for 56% to 57% of the judges' comments, where chance alone would give under 2%. Claude's comments also contain fewer hedges than the judges', and Qwen3-8B's have a markedly more positive tone. The words most typical of Claude's feedback are plan, willingness, may, overall, support, sizing; of the judges', like, see, want, plus, organized, numbers.
- **What goes with higher scores: how a summary is written matters less than what the venture is for the judges' scores, but more for Claude's.** We asked how much of the differences in scores between summaries two groups of features can predict: the summary's *form* (its length, readability, hedging, confident wording, numbers, and the team writing as "we") and the venture's *substance* (its type of product, milestones reached, legal entity and website). Form predicts 26% of the differences in the judges' scores and 70% in Claude's; substance predicts 41% and 23%. 
- **Where Claude's scores and the judges' disagree is partly predictable.** All 16 features together predict 48% of the differences between Claude's scores and the judges', and only 12% after allowing for the prediction that 16 features would produce by chance alone (the *adjusted* figure). No single feature stands out.
- **Who advanced.** Advancement follows the judges' scores. Neither AI judge's scores add to predicting it, and neither does any feature of the summary or the venture.
- **Novelty and topics can only be described.** Novelty (how different a summary is from the year's other summaries) was measured with each of the three embedding models. Their scores agree only moderately and are therefore averaged; the average has a reliability of 0.64 (on the same 0-to-1 scale as above). To check that the models' similarity measures are meaningful without human coders, we used the teams' own choices of fields on the application form: pairs of ventures that chose the same fields are more similar under all three models than pairs with nothing in common, by 0.73 to 1.06 standard deviations, a moderate gap. Without human ratings of novelty, the framework keeps novelty out of statistical tests; novelty is therefore only described.

## 1. The human benchmark (task 4.1)

**What it asks.** How much do the human judges agree with one another? Their agreement is the yardstick for the AI judges: an AI judge whose scores agree with the judges' as closely as the judges' scores agree among themselves performs as well as one more judge.

**The measures.**
- *ICC(1), the intraclass correlation*: the share of the variation in scores that reflects real differences between entries rather than disagreement among judges. 0 means the judges agree no more than chance; 1, perfectly. *One judge* is the reliability of a single judge's score; *three*, of the average of three.
- *Variance shares*: a statistical model (with crossed random effects for entries and judges) divides the variation in scores into differences between entries, which the scores should capture; each judge's overall severity, some judges scoring everyone higher or lower (*level noise*); and each judge's reactions to particular entries, with any other error (*pattern noise*). Judges were assigned to entries at random; severity is therefore not confounded with the quality of the entries a judge saw.
- *One judge vs two*: the correlation between one judge's score and the average of the entry's other two judges, over all three judges of each entry. Section 2 compares the AI judges with this number.

**How it fits.** The summary's first point; the benchmark for Sections 2 and 3.

Each entry was scored by three of the 15 judges.

| Criterion | Mean | SD | ICC(1) one judge | ICC(1) three | Share of variance: between entries | Judge severity (level noise) | Judge reactions to entries (pattern noise) | One judge vs two |
|---|---|---|---|---|---|---|---|---|
| Concept | 6.53 | 2.38 | 0.28 | 0.53 | 28% | 27% | 45% | 0.34 |
| Business model | 5.71 | 2.16 | 0.18 | 0.40 | 19% | 28% | 53% | 0.23 |
| Market | 6.03 | 2.38 | -0.01 | -0.03 | 5% | 35% | 60% | -0.03 |
| Written work | 6.08 | 2.24 | 0.16 | 0.36 | 19% | 27% | 54% | 0.20 |
| Investor interest | 5.50 | 2.48 | 0.07 | 0.19 | 15% | 40% | 45% | 0.09 |
| Weighted score | 5.91 | 2.06 | 0.10 | 0.25 | 14% | 38% | 48% | 0.13 |

*Source: `human_benchmark`, configuration `b8e6843ee4d3`, output `eec8e90504f7`.*

## 2. Scores (task 4.2, A1)

**What it asks.** How closely do the AI judges' scores match the human judges'? How consistent are each AI judge's scores across runs? Do the scores of human and AI judges distinguish the five criteria, or treat them all alike?

**The measures.**
- *Human mean, AI mean, difference*: average scores over the entries; a negative difference means the AI judge's scores are lower.
- *r with human mean*: the correlation between the AI judge's score, averaged over its five runs, and the average of the three judges.
- *Judge vs two, AI vs two, one run vs two*: correlations with the average of two judges, for the third judge, for the AI judge's average, and for a single AI run. They put the AI judge and one more human judge on the same footing. *AI minus judge* is the difference, with its 95% interval.
- *ICC across runs*: how consistent the AI judge's scores are across its five runs, from 0 to 1. *Same score in all runs*: the share of entries where all five runs gave the same score.
- *Halo*: the tendency of one overall impression to colour all five scores, measured by the average correlation among an evaluation's five scores; the *first eigenvalue share* is how much of their variation one general factor captures. The *multitrait-multimethod* comparison tests whether the scores of a criterion agree across humans and AI more than different criteria do; if not, the scores of both mostly reflect one general impression.

**How it fits.** The summary's second to fourth points: agreement, score levels and consistency, and halo; findings 1 to 3 in Section 8.

**Claude Sonnet 5.5**

| Criterion | Human mean | AI mean | Difference | r with human mean | Judge vs two | AI vs two | One run vs two | AI minus judge | ICC across runs | Same score in all runs |
|---|---|---|---|---|---|---|---|---|---|---|
| Concept | 6.53 | 6.03 | -0.51 | 0.59 | 0.34 | 0.53 | 0.56 | +0.19 [+0.00, +0.44] | 0.95 | 75% |
| Business model | 5.71 | 4.37 | -1.34 | 0.53 | 0.23 | 0.46 | 0.46 | +0.23 [+0.06, +0.45] | 0.96 | 80% |
| Market | 6.03 | 4.10 | -1.94 | 0.17 | -0.03 | 0.14 | 0.10 | +0.16 [-0.11, +0.46] | 0.94 | 78% |
| Written work | 6.08 | 7.17 | +1.09 | 0.37 | 0.20 | 0.33 | 0.32 | +0.13 [-0.07, +0.39] | 0.97 | 65% |
| Investor interest | 5.50 | 4.54 | -0.96 | 0.36 | 0.09 | 0.31 | 0.33 | +0.22 [-0.01, +0.50] | 0.97 | 75% |
| Weighted score | 5.91 | 4.98 | -0.94 | 0.52 | 0.13 | 0.44 | 0.45 | +0.32 [+0.14, +0.55] | 0.99 | 28% |

Halo: the five scores of one evaluation correlate 0.70 on average for a judge and 0.60 for one run (first eigenvalue: 76% and 70% of the total). Multitrait-multimethod, on entry means: the same criterion across methods correlates 0.40, different criteria across methods 0.35, different criteria within the judges 0.65 and within the AI 0.62.

*Source: `score_agreement`, configuration `949c5d14c563`, output `d99b2f5c1269`.*

**Qwen3-8B**

| Criterion | Human mean | AI mean | Difference | r with human mean | Judge vs two | AI vs two | One run vs two | AI minus judge | ICC across runs | Same score in all runs |
|---|---|---|---|---|---|---|---|---|---|---|
| Concept | 6.53 | 8.91 | +2.37 | 0.37 | 0.34 | 0.33 | 0.30 | -0.01 [+nan, +nan] | 0.46 | 82% |
| Business model | 5.71 | 7.20 | +1.49 | 0.39 | 0.23 | 0.35 | 0.32 | +0.12 [-0.10, +0.39] | 0.91 | 88% |
| Market | 6.03 | 7.55 | +1.52 | 0.18 | -0.03 | 0.14 | 0.07 | +0.17 [-0.13, +0.48] | 0.66 | 68% |
| Written work | 6.08 | 7.96 | +1.88 | 0.39 | 0.20 | 0.34 | 0.29 | +0.14 [-0.05, +0.38] | 0.88 | 50% |
| Investor interest | 5.50 | 7.25 | +1.75 | 0.25 | 0.09 | 0.21 | 0.17 | +0.12 [-0.22, +0.48] | 0.88 | 80% |
| Weighted score | 5.91 | 7.70 | +1.79 | 0.39 | 0.13 | 0.33 | 0.32 | +0.21 [-0.01, +0.50] | 0.94 | 25% |

Halo: the five scores of one evaluation correlate 0.70 on average for a judge and 0.41 for one run (first eigenvalue: 76% and 56% of the total). Multitrait-multimethod, on entry means: the same criterion across methods correlates 0.32, different criteria across methods 0.26, different criteria within the judges 0.65 and within the AI 0.50.

*Source: `score_agreement`, configuration `949c5d14c563`, output `30e2741700a8`.*

## 3. Rankings, selections and the cutoff (task 4.3, A2 and A3)

**What it asks.** If the entries were ranked by an AI judge's scores and as many were selected as advanced, would the same entries be selected? Do the evaluations of human and AI judges agree on the strongest entries but diverge near the cutoff for advancing, as the design expected?

**The measures.**
- *Rank correlation*: Spearman's and Kendall's correlations between the ranking by the AI judge's scores and the ranking by the judges' (1 is the same order).
- *Overlap*: how many entries two selections share, each as large as the number that advanced: the selection by AI scores against those that advanced, and against the judges' own top. Where advancement departs from the judges' ranking, as when entries that missed a requirement of the process are skipped, the judges' own top is the cleaner comparison.
- *Would gain, would lose*: entries that a selection by AI scores would include but that did not advance, and the reverse; their median place in the judges' ranking shows where they stand.
- *Testing the expectations*: each judge of an entry is held out in turn, and the average of the other two ranks the entries (the *reference*). Among the ten strongest entries by the reference, and among those near the cutoff (within ten places of it), the table compares how far the rank from the AI judge's scores is from the reference with how far the held-out judge's is (*rank difference*, in places), and how often each ranking places an entry on the other side of the cutoff. A negative *AI minus judge* means that the AI judge's ranks are closer to the two judges' than a third judge's are.

**How it fits.** The summary's points on selections and the expectations; findings 4 and 5 in Section 8.

| | Claude Sonnet 5.5 | Qwen3-8B |
|---|---|---|
| Entries ranked | 40 | 40 |
| Rank correlation with the judges' mean (Spearman; Kendall) | 0.50; 0.33 | 0.40; 0.28 |
| AI selection of 12: also advanced | 6 | 8 |
| AI selection: also in the judges' top 12 | 6 | 8 |
| Judges' top 12: also advanced | 12 | 12 |
| Would gain under AI selection (advanced: no) | 6 | 4 |
| Would lose under AI selection (advanced: yes) | 6 | 4 |
| Median judges' rank of those who would gain; of those who would lose | 22; 8 | 23; 6 |

The codes of those who would gain and lose are in the component's output, for Phase 5 (A5).

**The expectations (A3).** Each judge of an entry is held out in turn; the mean of the other two ranks the entries (the reference). In each band of reference positions, the table compares the absolute rank difference of the AI judge's ranking from the reference with the held-out judge's, and the share of entries each ranking places on the other side of the cutoff. Differences are the AI minus the judge, with 95% bootstrap intervals over entries.

**Claude Sonnet 5.5** (bands: strongest, reference rank 1 to 10; cutoff, reference rank 2 to 22)

| Band | Measure | AI | Held-out judge | AI minus judge |
|---|---|---|---|---|
| strongest | Rank difference, mean of runs | 9.48 | 15.30 | -5.82 [-10.17, -2.30] |
| strongest | Rank difference, one run | 9.23 | 15.30 | -6.07 [-10.42, -2.62] |
| strongest | Other side of the cutoff | 0.50 | 0.63 | -0.13 [-0.40, +0.11] |
| cutoff | Rank difference, mean of runs | 9.74 | 12.25 | -2.52 [-5.14, -0.22] |
| cutoff | Rank difference, one run | 9.65 | 12.25 | -2.60 [-5.26, -0.28] |
| cutoff | Other side of the cutoff | 0.43 | 0.41 | +0.02 [-0.15, +0.19] |

*Source: `ranking_comparison`, configuration `6c33921c79b6`, output `685157c3df05`.*

**Qwen3-8B** (bands: strongest, reference rank 1 to 10; cutoff, reference rank 2 to 22)

| Band | Measure | AI | Held-out judge | AI minus judge |
|---|---|---|---|---|
| strongest | Rank difference, mean of runs | 8.77 | 15.30 | -6.53 [-12.10, -2.04] |
| strongest | Rank difference, one run | 9.57 | 15.30 | -5.73 [-11.38, -1.11] |
| strongest | Other side of the cutoff | 0.43 | 0.63 | -0.20 [-0.50, +0.07] |
| cutoff | Rank difference, mean of runs | 10.44 | 12.25 | -1.82 [-5.15, +1.13] |
| cutoff | Rank difference, one run | 11.02 | 12.25 | -1.23 [-4.76, +1.69] |
| cutoff | Other side of the cutoff | 0.40 | 0.41 | -0.02 [-0.19, +0.16] |

*Source: `ranking_comparison`, configuration `6c33921c79b6`, output `f3a0cb38d5bf`.*

## 4. Written feedback (task 4.4, A4)

**What it asks.** Do the AI judges' written comments discuss the same issues as the human judges' comments on the same entry? Are they more uniform across entries, and tied more closely to the summary? How do they differ in length, hedging, tone and vocabulary?

**The measures.**
- *Embeddings and cosine similarity*: an embedding model turns a text into a list of numbers that captures its meaning; the cosine similarity of two such lists runs from about 0 (unrelated) to 1 (the same meaning). Three models from different families are used, and only patterns found with all three are treated as findings.
- *Specificity*: the similarity of two comments on the same entry minus that of comments on different entries. It shows whether two sources discuss *this* entry's issues, and is much less affected than raw similarity by the AI judges' far longer texts.
- *Alike across entries*: the average similarity of one source's comments on different entries; higher means more uniform, template-like feedback.
- *Fit to the summary*: a comment's similarity to its own summary minus its average similarity to the other summaries; *own ranked first* is how often the summary a comment most resembles is its own.
- *Embedders' agreement*: the correlation between the three models' similarity patterns over the same texts. *Re-execution*: whether embedding the texts again, in a new container, gives identical numbers.
- *Hedges*: words that soften a claim (may, perhaps, seems), per 100 words. *Tone*: a dictionary score of positive against negative wording, from −1 to 1. *Distinctive words*: words much more frequent in one source than in the other, allowing for how common each word is.

**How it fits.** The summary's point on feedback; finding 6 in Section 8.

The three embedders are Qwen3-Embedding-8B, given a task instruction, bge-m3 and gte-modernbert-base, run on Modal at pinned commits. The table pools the five written questions; each row is one embedder.

| Embedder | Specificity: judge–judge | judge–Claude | judge–Qwen | Claude–Claude (runs) | Alike: judges | Alike: Claude | Alike: Qwen | Fit: judges | Fit: Claude | Fit: Qwen |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen3 | 0.134 | 0.108 | 0.096 | 0.208 | 0.613 | 0.706 | 0.636 | 0.100 | 0.203 | 0.294 |
| bge_m3 | 0.117 | 0.090 | 0.082 | 0.168 | 0.634 | 0.735 | 0.706 | 0.081 | 0.152 | 0.211 |
| gte_modernbert | 0.114 | 0.099 | 0.082 | 0.197 | 0.691 | 0.740 | 0.741 | 0.089 | 0.180 | 0.221 |

Holds across all three embedders (design, Section 3: only such findings are reported as findings):

- Claude's feedback is more alike across entries than the judges': holds for all three.
- Claude's feedback fits its own summary better than the judges' does: holds for all three.
- A judge's comments and Claude's address the entry's issues more specifically than two judges' comments do: holds for none.

Lengths differ widely (mean words, all questions): judges 50; Claude Sonnet 5.5 592; Qwen3-8B 359. The judges' comments are short; the AI judges' outputs are essay-length.

*Source: `feedback_comparison`, configuration `0f150cecba49`, output `23879eac6df4`.*
*Source: `feedback_comparison`, configuration `0f150cecba49`, output `358e300052b8`.*
*Source: `feedback_comparison`, configuration `0f150cecba49`, output `2065c8c01e83`.*

**Do the embedders agree?** Spearman correlations between their pairwise similarities over the same texts (a random sample of the feedback; all summaries).

| Pair of embedders | Feedback | Summaries |
|---|---|---|
| bge_m3 and gte_modernbert | 0.78 | 0.51 |
| bge_m3 and qwen3 | 0.72 | 0.55 |
| gte_modernbert and qwen3 | 0.71 | 0.52 |

*Source: `embedding_agreement`, configuration `f55b25729683`, output `afcc028f37ab`.*
*Source: `embedding_agreement`, configuration `f55b25729683`, output `730b96bb7221`.*

**Re-execution.** The 40 summaries embedded again in a new container gave bge_m3: bit-identical vectors; gte_modernbert: bit-identical vectors; qwen3: bit-identical vectors.

**Text analysis.** Mean words, hedges per 100 words (Hyland 2005), and tone (VADER compound score, from −1 to 1; Hutto & Gilbert 2014), by question.

| Question | Words: judges | Claude | Qwen | Hedges: judges | Claude | Qwen | Tone: judges | Claude | Qwen |
|---|---|---|---|---|---|---|---|---|---|
| Q1 concept | 48 | 445 | 210 | 1.4 | 2.4 | 0.8 | 0.26 | 0.33 | 0.74 |
| Q3 business model | 51 | 651 | 456 | 2.4 | 2.5 | 1.8 | -0.04 | 0.37 | 0.93 |
| Q5 market | 46 | 606 | 360 | 4.6 | 2.7 | 1.7 | 0.15 | 0.72 | 0.98 |
| Q8 written work | 46 | 609 | 292 | 2.1 | 1.9 | 2.1 | 0.52 | 0.87 | 0.98 |
| Q10 investor interest | 45 | 459 | 373 | 1.5 | 2.2 | 1.3 | 0.21 | 0.49 | 0.88 |

Words most typical of the judges' feedback and of Claude's, by question (log-odds with an informative Dirichlet prior; Monroe, Colaresi & Quinn 2008). A word must appear in feedback on at least five entries and cannot be a name.

| Question | Judges | Claude |
|---|---|---|
| Q1 concept | like, real, point, see, nice, plus, sensible, start, smart, good | uniqueness, pay, willingness, quality, overall, concept, may, compelling, plan, weaknesses |
| Q3 business model | subscription, look, plus, dollar, slow, pricing, see, pick, fine, want | market, business, viability, validation, assumptions, willingness, sizing, likely, problem, key |
| Q5 market | exit, unclear, sizing, like, big, acquirer, path, number, looks, though | revenue, support, plan, attractiveness, model, value, hardware, group, economics, pain |
| Q8 written work | organized, numbers, well, cut, easy, say, clear, proofread, readable, like | plan, team, clarify, claim, whether, sales, state, value, submission, explain |
| Q10 investor interest | want, strengths, weaknesses, paying, pilot, see, working, prototype, team, back | sizing, may, overall, plus, interest, likely, support, willingness, month, execution |

*Source: `feedback_text`, configuration `13999668c3f8`, output `05fe6638b790`.*

## 5. Measures (tasks 5.1 and 5.2)

**What it asks.** Which measures of the summaries are used to explain the scores in Section 6, and how far can each be trusted without human coders?

**The measures.**
- *Style and language*: length; readability (*Flesch reading ease*, where higher is easier and 30 to 50 is college level, and the equivalent school *grade*); hedges and *boosters*, words that strengthen a claim (clearly, must); *numbers*, amounts and percentages; and *we, our, us*, the team speaking in its own voice; all per 100 words.
- *Novelty*: how far a summary is in meaning from its five most similar summaries of the year. The three models' scores are averaged into a *composite*; their agreement, and the composite's *reliability* by the Spearman-Brown formula (as for averaging several raters), show how stable it is.
- *Known-groups check*: without human ratings, similarity is checked against the teams' own categories. Pairs of ventures that chose at least two of the same fields on the application form should look more similar than pairs with nothing in common. The *standardized difference* is the gap in standard deviations; 0.8 counts as large.
- *Topics*: groups of similar summaries. The *silhouette* measures how well separated the groups are (from −1 to 1; near 0 means weak structure), and the *adjusted Rand index* how far the three models' groupings agree (0 is chance, 1 identical).

**How it fits.** The summary's point on the content measures. Novelty and topics have no human validation; they are therefore described, not tested (Section 9).

**Style and language profile** of the 40 summaries (code only, no model).

| Measure | Mean | SD | Min | Max |
|---|---|---|---|---|
| Words | 1125.7 | 81.6 | 899.0 | 1303.0 |
| Flesch reading ease | 51.0 | 7.3 | 31.7 | 64.1 |
| Flesch-Kincaid grade | 11.3 | 1.2 | 9.0 | 14.1 |
| Hedges per 100 words | 1.8 | 0.4 | 1.0 | 3.0 |
| Boosters per 100 words | 0.5 | 0.2 | 0.1 | 1.2 |
| Numbers per 100 words | 1.5 | 2.1 | 0.0 | 7.7 |
| We, our, us per 100 words | 4.3 | 1.1 | 2.3 | 6.5 |

1 of 35 PDFs exceed the two-page limit.

*Source: `style_profiler`, configuration `19cc68ed388c`, output `b15635a8c3e3`.*

**Novelty** is each summary's distance from its five most similar summaries of the year; the composite averages the three embedders' standardized scores. The embedders' novelty scores agree with a mean Spearman correlation of 0.37; the composite's reliability is accordingly 0.64. No human ratings of novelty exist in this study; novelty is therefore described, not tested.

*Source: `novelty_composite`, configuration `55de030f5250`, output `8739f0a5893a`.*

**Similarity, checked against the teams' own categories.** Pairs of judged summaries whose teams chose at least two of the same fields, against pairs with no field and no type of product in common; the threshold, set before the check, was a 95% interval excluding zero.

| Embedder | Pairs (same; nothing in common) | Mean similarity (same; nothing) | Difference | Standardized | Correlation with category overlap | Passed |
|---|---|---|---|---|---|---|
| bge_m3 | 48; 167 | 0.641; 0.605 | +0.036 [+0.010, +0.058] | 1.06 | 0.22 | yes |
| gte_modernbert | 48; 167 | 0.643; 0.614 | +0.029 [-0.002, +0.063] | 0.73 | 0.14 | no |
| qwen3 | 48; 167 | 0.550; 0.514 | +0.036 [+0.010, +0.062] | 0.90 | 0.26 | yes |

*Source: `similarity_known_groups`, configuration `8a8118be82dc`, output `6e0ab5f2b681`.*

**Topics.** Ward clusters of each embedder's whitened vectors, the number chosen by the silhouette: qwen3 8 topics (silhouette 0.25); bge_m3 8 topics (silhouette 0.25); gte_modernbert 8 topics (silhouette 0.26). The embedders' topics agree only modestly (adjusted Rand index 0.14, 0.16, 0.18); topics are therefore descriptive. The topics of Qwen3-Embedding, by their most distinctive words:

| Topic | Summaries | Distinctive words |
|---|---|---|
| 1 | 7 | parents, children, families, programs, child, parent, kids, kitchen |
| 2 | 6 | home, sensor, sensors, dollars, units, hardware, inside, kits |
| 3 | 7 | students, neighborhoods, summer, neighborhood, options, campus, rent, retail |
| 4 | 3 | month, per, staff, lost, summers, industry, sales, six |
| 5 | 6 | clinics, health, patients, patient, services, paper, healthcare, medication |
| 6 | 4 | data, firms, actually, year, staff, studies, sign, pilots |
| 7 | 3 | customers, big, people, fit, size, better, customer, scale |
| 8 | 4 | waste, campus, sustainability, impact, dashboard, partners, small, space |

*Source: `topics`, configuration `2baf4b9aec68`, output `9d4d07d066f6`.*
*Source: `topic_agreement`, configuration `f7929ecb666b`, output `d5a3169c66c8`.*

## 6. What explains the scores (task 5.3, A5)

**What it asks.** Which features of a summary's *form* (length, readability, hedging, numbers, voice) and of the venture's *substance* (products, milestones, legal entity, website) go with higher scores from the judges and from Claude? Which explain where Claude's scores and the judges' disagree, and which predict advancing?

**The measures.**
- *Variance explained (R²)*: the share of the differences in scores that the features account for, from 0 to 1, for form alone, substance alone and both; *adjusted* corrects for the number of features. *Form minus substance* compares the two groups, with a 95% interval.
- *Divergence*: Claude's standardized score minus the judges'. A feature that raises divergence is associated with relatively higher scores from Claude than from the judges.
- *Coefficients*: how many standard deviations the score moves with one standard deviation of a continuous feature, or when a yes-or-no feature is present, holding the other features fixed; 95% intervals robust to unequal variances (HC3). Bold marks intervals that exclude zero.
- *Linear probability model*: how each feature changes the probability of advancing, holding the judges' score fixed.
- *Novelty profile*: average scores in each fifth of the entries ordered by novelty; a description only, since novelty has no human validation.

**How it fits.** The summary's points on form and substance, divergence and advancement; findings 7 to 10 in Section 8.

40 judged entries; scores are standardized.

| Outcome | Form | Substance | Both | Both, adjusted | Form minus substance |
|---|---|---|---|---|---|
| Judges | 0.26 | 0.41 | 0.69 | 0.48 | [-0.48, +0.08] |
| Claude Sonnet 5.5 | 0.70 | 0.23 | 0.81 | 0.67 | [+0.02, +0.57] |
| Qwen3-8B | 0.49 | 0.21 | 0.61 | 0.35 | [-0.22, +0.46] |
| Divergence, Claude | 0.17 | 0.29 | 0.48 | 0.12 | [-0.50, +0.19] |
| Divergence, Qwen3-8B | 0.09 | 0.26 | 0.39 | -0.03 | [-0.53, +0.12] |

Claude minus the judges, in variance explained (95% intervals): both [-0.07, +0.25]; form [+0.14, +0.59]; substance [-0.38, +0.16].

Coefficients in the model with both groups (standardized outcome; continuous features standardized, binary ones 0 or 1), with 95% intervals (HC3). In bold, intervals that exclude zero.

| Feature | Judges | Claude | Divergence |
|---|---|---|---|
| log words | +0.32 [-0.00, +0.64] | +0.37 [-0.07, +0.80] | +0.05 [-0.53, +0.63] |
| flesch reading ease | **-0.77 [-1.51, -0.04]** | **-0.51 [-0.95, -0.07]** | +0.26 [-0.64, +1.16] |
| hedges per 100 words | +0.18 [-0.19, +0.56] | +0.20 [-0.06, +0.46] | +0.02 [-0.42, +0.46] |
| boosters per 100 words | +0.04 [-0.44, +0.51] | -0.09 [-0.43, +0.26] | -0.12 [-0.69, +0.44] |
| numbers per 100 words | **+0.81 [+0.36, +1.27]** | **+0.93 [+0.49, +1.38]** | +0.12 [-0.47, +0.70] |
| we per 100 words | **+0.99 [+0.03, +1.95]** | +0.43 [-0.21, +1.07] | -0.57 [-1.67, +0.53] |
| internet consumer tech | -0.21 [-0.87, +0.46] | +0.38 [-0.13, +0.89] | +0.59 [-0.26, +1.43] |
| product software app | -0.15 [-0.87, +0.58] | -0.16 [-0.80, +0.48] | -0.01 [-0.95, +0.93] |
| product physical product | +0.10 [-0.58, +0.78] | +0.03 [-0.63, +0.69] | -0.07 [-1.05, +0.91] |
| product data analytics | **+0.87 [+0.02, +1.71]** | +0.33 [-0.39, +1.05] | -0.54 [-1.58, +0.51] |
| product service | **-0.95 [-1.87, -0.03]** | -0.23 [-0.91, +0.45] | +0.72 [-0.43, +1.86] |
| milestones reached | +0.19 [-0.26, +0.63] | **+0.39 [+0.11, +0.68]** | +0.21 [-0.25, +0.67] |
| milestone first client has paid | -0.28 [-1.39, +0.83] | -0.42 [-1.43, +0.59] | -0.14 [-1.65, +1.37] |
| milestone funding raised | +0.44 [-0.79, +1.66] | -0.01 [-1.32, +1.30] | -0.45 [-2.02, +1.12] |
| entity formed | -0.37 [-1.27, +0.53] | -0.07 [-0.65, +0.52] | +0.30 [-0.84, +1.45] |
| has website | **+0.75 [+0.13, +1.37]** | +0.23 [-0.27, +0.74] | -0.51 [-1.39, +0.36] |

**Who advanced** (12 of 40). In a linear probability model with the judges' score and every feature, one standard deviation of the judges' score raises the probability of advancing by 0.31 [-0.03, 0.64]; no feature's interval excludes zero. Added to the judges' score, Claude Sonnet 5.5's score changes it by +0.03 [-0.09, +0.15]; Qwen3-8B's score changes it by +0.09 [-0.01, +0.18].

*Source: `score_explanation`, configuration `421b67a38799`, output `80be83454bc7`.*

**Novelty and the scores: a description, not a test.** Mean weighted scores and the share advanced in each fifth of the entries by the novelty composite.

| Fifth by novelty | Entries | Judges | Claude | Qwen3-8B | Advanced |
|---|---|---|---|---|---|
| 1 | 8 | 5.27 | 4.71 | 7.54 | 0% |
| 2 | 8 | 5.76 | 4.67 | 7.59 | 12% |
| 3 | 8 | 5.95 | 5.27 | 7.88 | 38% |
| 4 | 8 | 6.66 | 5.49 | 7.77 | 62% |
| 5 | 8 | 5.92 | 4.74 | 7.72 | 38% |

*Source: `novelty_profile`, configuration `45cfb1e8a6bb`, output `52b61a624b54`.*

## 7. Change over the years (A6)

The synthetic competition has one edition. In the project, A6 studies how human and AI evaluations change over the editions since 2019 (plan, task 7.3).

## 8. Findings to test on further years (task 5.5)

These are the findings of the 2019 records. The estimates that follow each are the synthetic competition's, whose judges are simulated; they therefore show the components at work and confirm or refute nothing.

1. **An AI judge's scores agree with the panel's more closely than one more human judge's do.** Against the mean of two judges, the AI judge's weighted score (mean of five runs) correlates more highly than the third judge's. This year, Claude: 0.44 against 0.13; difference +0.32 [+0.14, +0.55].
2. **Claude's scores are lower than the judges'.** This year: -0.94 points on the weighted score.
3. **Halo is stronger in the human judges' scores than in Claude's.** This year: the five scores of one evaluation correlate 0.70 for a judge and 0.60 for a Claude run.
4. **The ranks of AI and human judges agree on the strongest entries at least as well as the judges' ranks agree among themselves.** This year, rank difference among the ten strongest: Claude 9.5, third judge 15.3; difference -5.8 [-10.2, -2.3].
5. **Near the advancement cutoff, an AI judge's ranks do not diverge from the judges' more than a third judge's do**, contrary to the design's expectation. This year: Claude's ranks 9.7 places from the reference, the third judge's 12.3; difference -2.5 [-5.1, -0.2].
6. **AI feedback is more specific to its entry, more alike across entries and more tied to its own summary than judges' feedback**, under every embedder (Section 4).
7. **Longer summaries receive higher scores from both the judges and Claude.** This year, per standard deviation of log length: judges +0.32 [-0.00, +0.64], Claude +0.37 [-0.07, +0.80].
8. **Denser, harder-to-read summaries receive relatively higher scores from Claude than from the judges.** This year, divergence per standard deviation of reading ease: +0.26 [-0.64, +1.16].
9. **Advancement follows the judges' score, and AI scores add nothing to it.** This year, Claude's score added to the judges': +0.03 [-0.09, +0.15].
10. **Novelty and scores** (once novelty is validated against human ratings): whether the inverted U of optimal distinctiveness appears. This year shows no clear pattern, by description only.

## 9. Caveats and future work

- One year: 40 judged summaries. The findings are exploratory until further years test them.
- The AI judge's score is the mean of five runs, which is more reliable than a single judge's score; the score of one run is reported beside it and yields nearly the same results.
- In the synthetic competition, the judges' top 30% by mean weighted score advance; the judges' own top and those who advanced therefore coincide.
- The AI judges' written answers are many times longer than the judges' comments. The embedding measures are built to be robust to length, but the embedders have no validation against human similarity ratings. Their similarities track the teams' own categories (Section 5).
- The text measures (hedging, tone) are dictionary counts, not validated for this genre.
- The synthetic summaries are plain PDF and Word files, and their texts are therefore extracted cleanly. The layouts of real summaries, which can disorder the extracted text, are not reproduced.
- No human coders were available. Novelty and topics are therefore described, not tested, and the framework's methodological check keeps them out of inference. The embedding similarities were checked against the teams' own categories instead.
- The A5 models test many coefficients on 40 entries; they are to be read as patterns to be tested on further years, not as findings.

**Future work.**
- Validate novelty and the similarities against two coders' ratings, with the protocol and thresholds of the plan's Section 3 (Later: human validation of the measures); then add novelty to A5's regressions with a bias correction.
- A6: change over the editions since 2019, including a break after ChatGPT's release in late 2022.
- Further years, to test the findings of Section 8 (Study B, B5).
- An outside researcher's reproduction of a headline result from the package alone (B4).

## Provenance

Every number above comes from a stored component output with a provenance record in `synthetic/data/store/provenance/`.

| Result | Component | Version | Configuration | Output | Provenance record |
|---|---|---|---|---|---|
| Human benchmark | `human_benchmark` | 1.1.0 | `b8e6843ee4d3` | `eec8e90504f7` | `3be5d7d4…` |
| A1, Claude Sonnet 5.5 | `score_agreement` | 1.0.0 | `949c5d14c563` | `d99b2f5c1269` | `1682d872…` |
| A1, Qwen3-8B | `score_agreement` | 1.0.0 | `949c5d14c563` | `30e2741700a8` | `d292dad7…` |
| A2 and A3, Claude Sonnet 5.5 | `ranking_comparison` | 1.0.0 | `6c33921c79b6` | `685157c3df05` | `98aa17c8…` |
| A2 and A3, Qwen3-8B | `ranking_comparison` | 1.0.0 | `6c33921c79b6` | `f3a0cb38d5bf` | `0d38cb32…` |
| A4 embeddings, qwen3 | `feedback_comparison` | 1.0.0 | `0f150cecba49` | `23879eac6df4` | `330e42c0…` |
| A4 embeddings, bge_m3 | `feedback_comparison` | 1.0.0 | `0f150cecba49` | `358e300052b8` | `c90401aa…` |
| A4 embeddings, gte_modernbert | `feedback_comparison` | 1.0.0 | `0f150cecba49` | `2065c8c01e83` | `195705be…` |
| Embedders' agreement, feedback | `embedding_agreement` | 1.0.0 | `f55b25729683` | `afcc028f37ab` | `b214e71d…` |
| Embedders' agreement, summaries | `embedding_agreement` | 1.0.0 | `f55b25729683` | `730b96bb7221` | `4a29e00c…` |
| A4 text analysis | `feedback_text` | 1.0.1 | `13999668c3f8` | `05fe6638b790` | `51c69e86…` |
| Style profile | `style_profiler` | 1.0.0 | `19cc68ed388c` | `b15635a8c3e3` | `3298d193…` |
| Novelty composite | `novelty_composite` | 1.0.0 | `55de030f5250` | `8739f0a5893a` | `6e6828b6…` |
| Similarity, known groups | `similarity_known_groups` | 1.0.0 | `8a8118be82dc` | `6e0ab5f2b681` | `bfc272d6…` |
| Topics, Qwen3-Embedding | `topics` | 1.0.0 | `2baf4b9aec68` | `9d4d07d066f6` | `60dc4c06…` |
| Topic agreement | `topic_agreement` | 1.0.0 | `f7929ecb666b` | `d5a3169c66c8` | `3f826703…` |
| A5 | `score_explanation` | 1.0.0 | `421b67a38799` | `80be83454bc7` | `8d6faac2…` |
| Novelty profile | `novelty_profile` | 1.0.0 | `45cfb1e8a6bb` | `52b61a624b54` | `d2379baa…` |
