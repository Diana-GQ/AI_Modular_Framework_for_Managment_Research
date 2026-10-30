# Study design: human and AI evaluations of business plan competition entries

This document describes the study that illustrates the framework, which the [README](../README.md#the-framework) summarizes. The study compares human and AI evaluations of the same business plans (Study A, the illustration) and audits whether its results can be reproduced (Study B). The code cites this document as *(design, Section N)*, or by the name of an analysis, such as *(design, A1)* or *(design, B4)*.

The sections cover:
- Section 1: the data;
- Section 2: the AI evaluations the study generates;
- Section 3: the components and their measures;
- Sections 4 and 5: Study A and Study B;
- Section 6: an optional later study;
- Sections 7 and 8: the safeguards and the open questions;
- Section 9: the sources.

---

## 1. The data

### 1.1 The competition

The data come from an annual business plan competition for university students in the United States. Teams of two to four students or recent graduates enter an early-stage, for-profit venture. The competition has three rounds:

1. **Screening.** Each team submits an application form and a two-page executive summary. Three judges score each summary and write feedback.
2. **Business plan.** About 40 teams advance and submit a ten-page business plan.
3. **Finals.** About ten teams present live, and one wins.

### 1.2 What is available

The records of round 1 of the 2019 competition:

- **The applications sheet.** One row per application: 339 started and 141 submitted. Each row has:
  - short structured answers: type of product and of company, fields, milestones reached, legal entity;
  - a one-line pitch and a description of the business of about 200 words;
  - whether the team advanced to round 2 (38 did).
- **The judging sheet.** 405 evaluations, three for each of 135 judged entries, by 64 judges who each evaluated between 1 and 12 summaries. One judged entry is missing from the applications sheet and has no summary, so 134 judged summaries are available. Each judge scored five criteria from 1 to 10 and wrote feedback:

| Criterion | What the judge is asked | Feedback (mean length) |
|---|---|---|
| Concept | The quality of the idea: whether it addresses a real need in a unique and compelling way | A discussion of the concept (60 words) |
| Business model | Viability and scalability: whether there is a clear path to making money and growing | A comment (50 words) |
| Market | Market attractiveness and exit potential | A comment (46 words) |
| Written work | The quality of the summary's writing, as a sign of the team's attention to detail and communication | What the team can do to improve the submission (40 words) |
| Investor interest | As an early-stage investor, the interest in taking the next step after reading only the summary | The strengths and weaknesses behind the score (38 words) |

- **The executive summaries.** 161 files: 149 PDFs, most of two pages (15 have more), and 12 Word files. The median summary has about 1,000 words. Every PDF has a text layer.

**Scoring and ranking.** Each evaluation has a weighted score: 0.2 × concept + 0.2 × business model + 0.2 × market + 0.1 × written work + 0.3 × investor interest. Entries are ranked by the mean of their three weighted scores, and entries with equal means share a rank.

**Advancement.** The highest-placed entries advance, except those that miss a requirement of the process, such as legally forming the business; their places go to the next entries (organizers). The 2019 records agree. Of the 38 entries that advanced, 26 were among the 38 highest placed, and the other 12 were all placed 39th to 54th. No entry placed lower advanced.

**Judges.** Judges are entrepreneurs, professors of entrepreneurship and others close to these fields, and they are assigned to entries at random (organizers). The records identify them, and the study replaces their identities with codes. Their assignments link all judges and entries into one connected network. That allows each judge's severity to be estimated on a common scale, and random assignment keeps it apart from the quality of the entries the judge saw.

**Other years.** The competition has run every year since 2019, its first edition. The records of the later editions can be obtained, though when is open (Section 8, question 1). They are assumed to have the same format. At about 135 judged entries a year, the editions to 2026 provide about 1,000.

**Later rounds.** The records of rounds 2 and 3, including who reached the finals and who won, cannot be obtained (organizers). The applications sheet does not record them either.

### 1.3 Analysis tables

The records are arranged in four tables linked by codes, and the AI judges' answers in a fifth:

- *entries*: one row per application, with the form's answers, and whether it was submitted, judged and advanced;
- *documents*: one row per executive summary, with its text and its page and word counts;
- *evaluations*: one row per entry, judge, question and run, with the score or the text;
- *judges*: one row per judge code, with no other attribute;
- *evaluations_ai*: the AI judges' answers in the form of *evaluations*, where the evaluator is the AI component, with each call's status and the configuration it ran under.

### 1.4 What the data allow and rule out

- **Evaluation, not venture success.** Advancing, reaching the finals and winning are human judgments too, and the ventures' later outcomes are not recorded. The questions therefore take the form "what do judges reward", never "which ventures are good".
- **Human and AI evaluations of the same summaries,** on the same questions (Section 2).
- **A benchmark from the judges themselves.** Three judges per entry, crossed in one network, show how much human judges disagree. Any difference between human and AI evaluations can be read against that disagreement.
- **A score and feedback for every criterion.** These allow halo to be measured. Halo is the tendency of one overall impression to colour every score.
- **A human measure of clarity.** The written-work criterion rates the writing itself.
- **A cohort per year,** which allows each venture's distinctiveness to be measured against the others.
- **What is ruled out.** No judge evaluates the same summary twice, so consistency across occasions is measured only for AI judges. Rounds 2 and 3 cannot be analysed, since their records cannot be obtained.

### 1.5 Personal data

The records give the names and email addresses of team members and judges, and the summaries name team members. The analysis tables carry codes instead, and the key that links codes to names is kept apart from them. The summaries, the feedback and data derived from them may not be published or shared outside the study (organizers). Aggregate statistics, such as counts, percentages and correlations, may be published. The competition platform also holds proofs of student status and tax forms; the study does not collect them. Section 7 gives the safeguards.

---

## 2. The AI evaluations

The study generates its own AI evaluations of every judged summary. The judges' questions are posed one per call, never several together, so that each output depends only on its own question.

### 2.1 Questions and prompts

Every call uses the authors' system prompt:

> You are an expert evaluator in entrepreneurship and early-stage venture assessment. You are analytical, objective, and concise but insightful. No fluff. You do not act as an assistant. You act as a structured evaluation engine.

and sends the summary's text and one question:

> Business plan text:
>
> {the summary's text}
>
> Question: {the question}

There are ten questions, two per criterion. The written questions are the authors' wording of the judges' feedback questions; the score questions are the judges' own wording. Both AI judges read them from [`components/shared/judge_prompts.yaml`](../components/shared/judge_prompts.yaml).

| Criterion | Written question | Score question, answered with an integer from 1 to 10 |
|---|---|---|
| Concept | Q1. Discuss the overall quality of the business concept or idea. Address whether the offering addresses a real and clearly identified pain or need in a unique and compelling way. | Q2. Please rate the quality of the company concept / idea on a scale of 1-10. |
| Business model | Q3. Comment on the viability and scalability of the business model and strategy. Address whether the company has a clear path to making money and growing, and evaluate the validity of the entrepreneur's assumptions. | Q4. Please rate the viability and scalability of the business model and strategy on a scale from 1-10. |
| Market | Q5. Share thoughts on market attractiveness and exit potential. Address whether the market would support this venture, whether the company targets the correct group, and whether the market is large enough to support scaling. | Q6. Please rate the market attractiveness and exit potential on a scale from 1-10. |
| Written work | Q8. What can the team do to improve their written submission? | Q7. Please rate the quality of the written work for this executive summary on a scale from 1-10. As this is generally an implicit indicator of the management team's attention to detail, communication skills, and language choice, this score should reflect your confidence in the team in these areas. |
| Investor interest | Q10. Share the strengths and weaknesses that you considered to arrive at your investment interest rating. | Q9. You are an early stage investor considering this as an investment opportunity. After reading the executive summary only, please rate your interest level on a scale from 1-10 in moving forward with this company to the next step of the investment process (i.e. seeing a full business plan, hearing them pitch, following up with questions, etc.). |

The service enforces the form of each answer; the prompt does not request it. Every answer can therefore be parsed:
- **Score questions.** The answer can only be an integer from 1 to 10.
- **Written questions.** The answer is free text. Claude returns it as the one text field of a JSON object (Anthropic's structured outputs). The open-weight model's output is plain text: when its output was held to JSON, generation sometimes stopped at the first line break and produced only blank space.

Q10 refers to an investment interest rating that, in a separate call, the model has not produced. In the pilot, about one in six of Claude's answers to Q10 states a rating, which may differ from the score it returned for Q9.

### 2.2 Models and runs

- **Claude Sonnet 5.5** (model ID `claude-sonnet-5-5`), through Anthropic's API, is the main AI judge.
  - *Recorded:* the model ID, the thinking setting (off), the effort level, the maximum output length, the prompts and the output format.
  - *What cannot be fixed:* the API accepts only the model's default sampling settings and has no random seed (Anthropic, 2026). Its outputs therefore vary from run to run. They can be reproduced from the store, but not re-executed exactly. No hosted model can be re-executed exactly, even where temperature and seed can be set, because servers group requests differently from run to run (He, 2025).
  - *Refusals and fallbacks:* fallbacks to other models are off, so every output comes from the named model. A refusal is recorded as a missing answer.
- **Qwen3-8B**, an open-weight model, is the re-executable counterpart.
  - A rented H100 GPU on Modal serves its weights, pinned to a commit, with vLLM 0.30.0 (Kwon et al., 2023) in batch-invariant mode. This mode removes the variation that comes from how servers batch requests (He, 2025).
  - It samples at temperature 0.7 (top-p 0.8, top-k 20), with seeds 1 to 5 for the five runs, so every run can be re-executed exactly.
  - Batch-invariant mode is still in beta in vLLM, and guarantees identical outputs only on the same hardware and engine version (vLLM project, 2026a, 2026b). The deployment ([`pipeline/modal_qwen.py`](../pipeline/modal_qwen.py)) therefore pins the GPU, the engine's container image and the model's commit, and a determinism test runs before each experiment.
- **Runs.** Each of the ten questions is posed to each model five times for each judged summary: 6,700 calls per model for the 134 judged summaries of 2019. The repeated runs show how much the outputs vary, and an AI score is the mean of its five runs.
- **Storage.** Every request and response is stored with its provenance record (framework, Section 5).

The services:
- **Modal** rents GPUs by the second, for the open-weight judge and the embedding models (Section 3).
- **Hugging Face** supplies the published weights and their commit identifiers. No data from the competition are sent to it.

---

## 3. Components

Twenty-three components produce every number of the study. Each has a contract and a card before its outputs enter an analysis.

| Role | Components |
|---|---|
| Extractors | `text_extractor` (PDF and Word files to text, with page and word counts); `records_tables` (the export, the code key and the texts to the four tables of Section 1.3, with codes in place of identities); `venture_characteristics` (the application form's answers, as indicators) |
| Judges | `claude_judge`; `qwen_judge`, re-executable exactly |
| Representers | three embedders, `embedder_qwen3`, `embedder_bge_m3` and `embedder_gte_modernbert` (a text to a vector from model M with instruction I); `style_profiler` (length, readability, hedges, boosters, numbers, the team's voice); `novelty`; `topics` |
| Validators | `human_benchmark`; `score_agreement`; `ranking_comparison`; `feedback_comparison`; `feedback_text`; `embedding_agreement`; `topic_agreement`; `similarity_known_groups`; `score_explanation` |
| Aggregators | `weighted_score` (the competition's weighted score); `novelty_composite` (the mean of three embedders); `novelty_profile` |

Four more components generate the synthetic competition (B4): `synthetic_competition`, `synthetic_concepts`, `synthetic_summary` and `synthetic_feedback`.

How the measures are built:

- **Embeddings.** An *embedding* is a list of numbers that represents a text's meaning; texts with similar meanings get similar lists.
  - One vector per summary and one per feedback text.
  - Three open-weight embedding models from different families, run on Modal with pinned weights, so that the vectors can be re-executed exactly: Qwen3-Embedding-8B (Zhang et al., 2025), which takes a task instruction as a prefix to the text; bge-m3, built on XLM-RoBERTa; and gte-modernbert-base, built on ModernBERT. Each text is embedded alone, so its vector does not depend on what else is embedded with it. Only findings that hold across the three models are reported, and their agreement is measured by correlating their pairwise distances (Kriegeskorte, Mur & Bandettini, 2008).
  - For topics, vectors are centred within each year and whitened to their leading components (Su et al., 2021). Novelty and similarity use the normalized vectors as they are: among the variants compared on 2019, this agreed best across the three embedders.
  - No embedding space is fine-tuned on the outcomes.
- **Language and clarity.**
  - Readability, hedging and confidence.
  - Word categories from validated dictionaries.
  - The expressions that most distinguish groups of summaries, found with a method that accounts for how common each word is (Monroe, Colaresi & Quinn, 2008).
  - The judges' written-work score is the human measure of clarity.
- **Content.**
  - Topics from clusters of the summaries' embeddings (Ward linkage, with the number of clusters chosen by the silhouette). The embedders' topics agree only modestly, so topics are used descriptively.
  - Novelty is each summary's distance from its five most similar summaries of the year. The primary measure averages the three embedders' standardized scores. With further years, similarity to earlier years' summaries is added (Kelly et al., 2021).
  - Semantic distance is a limited measure of novelty (Organisciak et al., 2023), and no human ratings of novelty are available in this study. Novelty is therefore described and kept out of inference until human ratings validate it (below).
- **Cautions.**
  - Length affects embeddings, so feedback is compared criterion by criterion and controlled for length.
  - Embeddings of feedback show what is discussed, not the verdict, which comes from the scores.
  - Cosine similarity can be misleading (Steck, Ekanadham & Kallus, 2024). Similarities are therefore checked against the teams' own categories on the application form: pairs whose teams chose the same fields should be more similar.
- **Validators.**
  - Intraclass correlations (Shrout & Fleiss, 1979).
  - A model with crossed random effects for entries and judges, as in generalizability theory (Brennan, 2001; Bates et al., 2015).
  - Halo, through the multitrait-multimethod logic of Campbell & Fiske (1959).
  - AI labels used in inference receive a bias correction (framework, Section 6): a correction, estimated on a human-coded sample, for the AI labels' errors.

**Human validation of the measures (future work).** No human coders were available, so novelty and the similarities have no human validation yet. The protocol is fixed in advance:
- Two coders, who see neither the AI measures nor the hypotheses, rate the novelty of 60 summaries drawn at random from the judged ones, and the similarity of 50 pairs among them. Half the pairs come from teams that chose at least two of the same fields on the application form, and half from teams with no field and no type of product in common. No AI measure therefore determines which pairs are rated.
- The acceptance thresholds are fixed before coding starts. Agreement between the coders must reach an ICC(2,2) of at least 0.70 for each task. Each measure must correlate with the coders' mean rating at 0.40 or more for novelty and 0.50 or more for similarity, with 95% intervals that exclude zero.
- Measures that pass enter A5's regressions, with a bias correction (framework, Section 6).

---

## 4. Study A: the illustration

The illustration tests the framework on the competition's records: every edition since 2019, about 1,000 judged summaries, of which 2019 is analysed here. It:
- compares human and AI scores, rankings, selections and written feedback, using embeddings and text analysis;
- examines whether human and AI judges agree on the strongest entries but diverge near the cutoff for advancing;
- explains divergence and convergence through the language, content and clarity of the summaries and the ventures' characteristics;
- tracks how the agreement between human and AI judges, and the summaries themselves, change over the editions, including after ChatGPT's release.

Many studies measure how accurate, consistent or efficient AI judges are (for example Stureborg et al., 2024; Liang et al., 2024; Csaszar, Ketkar & Kim, 2024; Katcharovski & Maxwell, 2025). The illustration asks a different question: what human and AI evaluations of the same summaries share, where they differ, why, and where they complement each other. Claude Sonnet 5.5 is the AI judge in its main tests, which are repeated with the open-weight model as a check (B3).

**Expectations:**
- the evaluations of human and AI judges agree on the strongest entries;
- they diverge near the cutoff for advancing, beyond what the human judges' own disagreement at the same positions would produce.

The analyses:

- **A1. Scores.** For each criterion and for the weighted score, how closely do the AI judge's scores, averaged over its five runs, agree with the human judges' scores?
  - *Benchmark.* How closely one human judge agrees with the other two. It comes from dividing the judges' disagreement into three parts (Kahneman, Sibony & Sunstein, 2021): differences between entries, each judge's overall severity (level noise), and each judge's reactions to particular entries (pattern noise).
  - *Qualifier: consistency across runs.* How consistent the AI judge's scores are across its five runs. LLM judges' outputs can flip on repeated trials (Yagubyan, 2026), and vary even at temperature zero (Tamba, 2026).
  - *Qualifier: halo.* The correlation among an evaluator's five scores, compared between humans and AI. The scores of LLM raters show anchoring across attributes (Stureborg et al., 2024; Sunkavalli, 2026).
  - *Gap.* Agreement between LLMs and humans is rarely benchmarked against agreement among humans in entrepreneurship. No study of the reliability of judging in university business plan competitions was found (searches covering 2015 to 2026).
- **A2. Rankings and selections.** Rank the entries by the AI judge's weighted score, and select as many of the highest-ranked entries as the human judges advanced. Measure the overlap, and identify who would gain and who would lose under AI selection.
- **A3. The strongest entries and the cutoff.** Test the two expectations. Rank differences are naturally larger where scores are clustered. The test therefore compares the disagreement between AI and human judges with the disagreement among the human judges at the same positions.
- **A4. Written feedback.** Compare the AI's and the judges' feedback on each criterion in two complementary ways.
  - *Embeddings* show whether they discuss the same issues: GPT-4's and human reviewers' comments on research papers overlapped by 31 to 39 percent (Liang et al., 2024). They also show whether AI feedback is more alike across entries than human feedback; LLM ratings vary less than human ratings (Zurawicki et al., 2026). Finally, they show whether feedback fits its own summary better than the others.
  - *Text analysis* compares length, tone, hedging and the recurring themes of praise and criticism.
- **A5. Why they converge or diverge.** Using the language, content and clarity measures (Section 3) and the ventures' characteristics from the applications sheet, ask:
  - which features explain the human scores, which explain the AI scores, and which explain where they disagree;
  - how the entries that advanced differ from those that did not.

  Two questions from entrepreneurship frame the analysis:
  - *Form versus substance.* Business plans barely influenced venture capital decisions (Kirsch, Goldfarb & Gera, 2009), but in a screening round the summary is the judges' only input.
  - *Optimal distinctiveness.* Is there an inverted U between novelty and scores (Zhao et al., 2017; Taeuscher, Bouncken & Pesch, 2021)? Evaluators can penalize novelty (Boudreau et al., 2016). Without human validation of novelty, the pattern is described, not tested.
- **A6. Change over the years.** With the editions since 2019, does the agreement between human and AI judges change from one year to the next, and do the summaries change?
  - *ChatGPT break.* The editions span ChatGPT's release in late 2022. Test for a break after it in the agreement between human and AI judges, and describe any in the summaries' distinctiveness. AI-generated ideas are less diverse (Terwiesch et al., 2026; see also Doshi & Hauser, 2024), and founders' access to ChatGPT lowers screening accuracy (Cowgill, Hernandez-Lagos & Wright, 2026). Novelty has no human validation, so its change is described, not tested.
  - *What is out of reach.* The finalists and winners cannot be obtained, so whether human or AI evaluations predict success beyond round 1 is not studied.

Every number reported in Study A has a provenance record.

---

## 5. Study B: the reproducibility audit

Study B tests, on the results of Study A, the four levels of reproducibility of the framework's Section 7: reproduce (the same data, code and stored AI outputs give the same numbers), re-execute (generating the AI outputs again gives the same outputs), robust (replacing a component with an equivalent leaves the conclusions intact) and replicate (the same measures on new data support the same conclusions). B4 tests the first level by an outside researcher.

- **B1. Reproduce.** Rebuild the analysis from the package, the repository with the sources and stored outputs: the code, contracts and cards, the sources, and the stored outputs and provenance records of the components that call a model. The rebuild runs in a fresh copy of the package, with a new environment built from its lock file. Every other output is computed again and compared with the original, as are the tables and reports. Measure the share reproduced bit for bit, the share equal only to within rounding or to within the precision a component's contract declares for an optimizer's outputs, and the time taken.
- **B2. Re-execute.** Rerun the open-weight judge from its stored configuration; the expectation is identical outputs. Rerun the Claude judge on a subsample while the model is still offered, and measure its agreement with the stored outputs, which measures drift.
- **B3. Substitute.** Swap each component for its equivalents and record which conclusions of Study A survive, as a multiverse analysis (Steegen et al., 2016). The swaps cover the Claude judge for the open-weight judge, each embedding model and post-processing option, and the text extractor.
- **B4. Outside reproduction.** The competition's records may not be shared, so this repository carries a synthetic dataset: a fictional competition of 40 ventures and 15 judges, and the results the pipeline produced on it ([`synthetic/`](../synthetic/README.md)).
  - *Scores.* The judges' scores are simulated with the variance components and halo of Study A's benchmark.
  - *Texts.* An AI model generates the ventures' names and concepts in a single call, so that they differ, and then each venture's application and summary and each simulated judge's comments.
  - *Keeping real names out.* No real record enters it. Every generated text is checked against the real records' list of identifying terms, and generated again if it matches.
  - *The test.* A researcher outside the study reproduces the results from this repository alone, and records the time taken and every problem met. This tests the repository's reproducibility, not the results on 2019.
- **B5. Replicate.** Run the frozen pipeline on each further year, and test whether the findings from earlier years hold.

B1 and B2 are piloted on a small subset of 2019 entries before the main runs.

---

## 6. Later study: porting (optional)

Once Studies A and B are complete, the components can be ported to public corpora, to test whether reuse saves validation effort (framework, Section 8): a component validated once can serve many studies, with a short re-validation in each new setting. The method is to validate the ported components again and compare the effort and accuracy with building the same measures from scratch.

- **The best public candidate:** the submissions to the ICLR 2024 machine-learning conference and their public reviews. Each review has scores, an overall rating and written text, and each paper an accept-or-reject decision; the reviews are released under CC BY 4.0 (OpenReview, 2024).
- **For the judge-severity validator:** an open dataset from another business plan competition (Xu & Kotha, 2025), in which 184 judges with stable identifiers evaluated 612 startups.
- **Alternatives:** archived Climate CoLab contest proposals (Malone et al., 2017) are closer in kind but survive only in web archives. A set of 147 research ideas scored from 1 to 10 with written rationales is another option (Si, Yang & Hashimoto, 2025).

---

## 7. Safeguards

- **Exploration and replication.** The analyses of 2019 are exploratory, and further years test what they suggest (B5). No AI configuration is chosen for its agreement with the human judges.
- **Validation.** Measurement uses of AI require validation against humans (Ludwig, Mullainathan & Rambachan, 2024). The AI judges are compared with the human judges and checked for consistency across runs (A1). No human coders are available for the content measures. Their similarities are checked against the teams' own categories, and novelty and topics are described but kept out of inference until human ratings validate them (Section 3). The authors spot-checked the text extractor.
- **Contracts and provenance.** Every component has a contract, which the pipeline enforces, and a card. The contract records model names, versions and every setting. Inputs are hashed, and every output has a provenance record.
- **Pseudonymization.** The analysis tables carry codes. The raw records and the key linking codes to names stay on the authors' machines, in `data/raw/` and the restricted folder `data/private/`. Nothing that identifies a person, a venture or an institution in the data enters this repository. An automatic check ([`scripts/check_sensitive.py`](../scripts/check_sensitive.py)) enforces this before every commit, against a list of terms built from the records.
- **Confidentiality of derived data.** Embeddings can be partly inverted to recover the text they encode (Morris et al., 2023). The code is published freely. The summaries, the feedback and derived data (AI outputs, vectors) are neither published nor shared outside the study; the repository carries a synthetic dataset instead (B4). Publications report aggregate statistics only, with no text from the records and nothing about any single entry or judge.
- **Data protection.**
  - The consent and competition terms allow summaries and feedback to be sent to paid commercial APIs.
  - Data go only through the study's paid accounts, never through chat apps, with data-sharing options off.
  - Uploaded files and batch inputs are deleted after each run, and the GPU deployments run only for the length of each run.
- **Cost.** Compute is modest.

Provider terms for paid API use, checked on 2026-10-04:

| Provider | Trains on API inputs | Default retention | Zero retention |
|---|---|---|---|
| Anthropic API (the Claude judge) | No | Up to 30 days | By agreement |
| Modal (the open-weight judge and the embedding models) | No: Modal states it "will never access or use" function inputs or outputs | Inputs and outputs up to 7 days; logs 1 day on the starter plan | Not offered; document text is kept out of logs |

---

## 8. Open questions

1. **When can the records of the editions since 2020 be obtained?** They determine when the findings of 2019 can be tested (B5) and the change over the years studied (A6).

---

## 9. Sources

**Embeddings and text measures**
- Hubert, L., & Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193–218. https://doi.org/10.1007/BF01908075
- Hutto, C., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *Proceedings of the International AAAI Conference on Web and Social Media*, 8(1), 216–225. https://doi.org/10.1609/icwsm.v8i1.14550
- Hyland, K. (2005). *Metadiscourse: Exploring interaction in writing*. Continuum.
- Kelly, B., Papanikolaou, D., Seru, A., & Taddy, M. (2021). Measuring technological innovation over the long run. *American Economic Review: Insights*, 3(3), 303–320. https://doi.org/10.1257/aeri.20190499
- Kriegeskorte, N., Mur, M., & Bandettini, P. (2008). Representational similarity analysis – connecting the branches of systems neuroscience. *Frontiers in Systems Neuroscience*, 2, 4. https://doi.org/10.3389/neuro.06.004.2008
- Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. *Political Analysis*, 16(4), 372–403. https://doi.org/10.1093/pan/mpn018
- Organisciak, P., et al. (2023). Beyond semantic distance. *Thinking Skills and Creativity*. https://doi.org/10.1016/j.tsc.2023.101356
- Steck, H., Ekanadham, C., & Kallus, N. (2024). Is cosine-similarity of embeddings really about similarity? *Companion Proceedings of the ACM Web Conference 2024*, 887–890. https://doi.org/10.1145/3589335.3651526
- Su, J., Cao, J., Liu, W., & Ou, Y. (2021). Whitening sentence representations for better semantics and faster retrieval. arXiv:2103.15316.
- Zhang, Y., Li, M., Long, D., Zhang, X., Lin, H., Yang, B., et al. (2025). Qwen3 Embedding: Advancing text embedding and reranking through foundation models. arXiv:2506.05176.

**Reliability and measurement**
- Bates, D., Mächler, M., Bolker, B., & Walker, S. (2015). Fitting linear mixed-effects models using lme4. *Journal of Statistical Software*, 67(1), 1–48. https://doi.org/10.18637/jss.v067.i01
- Brennan, R. L. (2001). *Generalizability Theory*. Springer. https://doi.org/10.1007/978-1-4757-3456-0
- Campbell, D. T., & Fiske, D. W. (1959). Convergent and discriminant validation by the multitrait-multimethod matrix. *Psychological Bulletin*, 56(2), 81–105. https://doi.org/10.1037/h0046016
- Kahneman, D., Sibony, O., & Sunstein, C. R. (2021). *Noise: A Flaw in Human Judgment*. Little, Brown Spark.
- Ludwig, J., Mullainathan, S., & Rambachan, A. (2024, rev. 2025). Large language models: An applied econometric framework. arXiv:2412.07031.
- Shrout, P. E., & Fleiss, J. L. (1979). Intraclass correlations: Uses in assessing rater reliability. *Psychological Bulletin*, 86(2), 420–428. https://doi.org/10.1037/0033-2909.86.2.420
- Steegen, S., Tuerlinckx, F., Gelman, A., & Vanpaemel, W. (2016). Increasing transparency through a multiverse analysis. *Perspectives on Psychological Science*, 11(5), 702–712. https://doi.org/10.1177/1745691616658637

**LLM judges and reproducibility**
- He, H. (2025). Defeating nondeterminism in LLM inference. Thinking Machines Lab. https://doi.org/10.64434/tml.20250910
- Liang, W., et al. (2024). Can large language models provide useful feedback on research papers? *NEJM AI*, 1(8). arXiv:2310.01783.
- Stureborg, R., et al. (2024). Large language models are inconsistent and biased evaluators. arXiv:2405.01724.
- Sunkavalli (2026). LLM judges as raters: Severity, halo, reliability, version instability in essay scoring. arXiv:2608.29517.
- Tamba (2026). Necessary but not sufficient: Temperature control and reproducibility. arXiv:2606.26185.
- Yagubyan (2026). The coin flip judge? arXiv:2606.13685.
- Zurawicki et al. (2026). PRAIB. arXiv:2605.29815.

**Serving models**
- Anthropic (2026). Claude API documentation: models, pricing and request parameters for Claude Sonnet 5.5. https://platform.claude.com/docs
- Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H., et al. (2023). Efficient memory management for large language model serving with PagedAttention. *Proceedings of the 29th Symposium on Operating Systems Principles (SOSP 2023)*, 611–626. https://doi.org/10.1145/3600006.3613165
- vLLM project (2026a). Batch invariance. https://docs.vllm.ai/en/latest/features/batch_invariance
- vLLM project (2026b). Reproducibility. https://docs.vllm.ai/en/latest/usage/reproducibility

**AI and human evaluation of ventures and ideas**
- Cowgill, B., Hernandez-Lagos, P., & Wright, N. L. (2026). Does AI cheapen talk? Theory and evidence from global entrepreneurship and hiring. CESifo Working Paper.
- Csaszar, F. A., Ketkar, H., & Kim, H. (2024). Artificial intelligence and strategic decision-making: Evidence from entrepreneurs and investors. *Strategy Science*. https://doi.org/10.1287/stsc.2024.0190
- Doshi, A. R., & Hauser, O. P. (2024). Generative AI enhances individual creativity but reduces the collective diversity of novel content. *Science Advances*, 10(28), eadn5290. https://doi.org/10.1126/sciadv.adn5290
- Katcharovski, Y., & Maxwell, A. L. (2025). Predicting business angel early-stage decision making using AI. arXiv:2507.03721.
- Terwiesch, C., Meincke, L., Girotra, K., Mollick, E., Nave, G., & Ulrich, K. (2026). AI and its impact on creativity and diversity. *Production and Operations Management*. https://doi.org/10.1177/10591478261474243

**Selection and novelty**
- Boudreau, K. J., Guinan, E. C., Lakhani, K. R., & Riedl, C. (2016). Looking across and looking beyond the knowledge frontier: Intellectual distance, novelty, and resource allocation in science. *Management Science*, 62(10), 2765–2783. https://doi.org/10.1287/mnsc.2015.2285
- Kirsch, D., Goldfarb, B., & Gera, A. (2009). Form or substance: The role of business plans in venture capital decision making. *Strategic Management Journal*, 30(5), 487–515. https://doi.org/10.1002/smj.751
- Taeuscher, K., Bouncken, R., & Pesch, R. (2021). Gaining legitimacy by being different: Optimal distinctiveness in crowdfunding platforms. *Academy of Management Journal*, 64(1), 149–179. https://doi.org/10.5465/amj.2018.0620
- Zhao, E. Y., Fisher, G., Lounsbury, M., & Miller, D. (2017). Optimal distinctiveness: Broadening the interface between institutional theory and strategic management. *Strategic Management Journal*, 38(1), 93–113. https://doi.org/10.1002/smj.2589

**Porting corpora**
- Malone, T. W., Nickerson, J. V., Laubacher, R. J., Fisher, L. H., de Boer, P., Han, Y., & Towne, W. B. (2017). Putting the pieces back together again: Contest webs for large-scale problem solving. *Proceedings of CSCW 2017*, 1661–1674. https://doi.org/10.1145/2998181.2998343
- OpenReview (2024). Terms of use, last updated 24 September 2024. https://openreview.net/legal/terms
- Si, C., Yang, D., & Hashimoto, T. (2025). Can LLMs generate novel research ideas? A large-scale human study with 100+ NLP researchers. ICLR 2025. arXiv:2409.04109.
- Xu, G., & Kotha, R. (2025). The LKY Global Business Plan Competition 2023 Open Dataset: 612 university startups from 63 countries evaluated by 184 judges with post-competition venture capital funding. SSRN. https://doi.org/10.2139/ssrn.5565518. Data: https://osf.io/78h4v

**Data protection and provider terms**
- Anthropic (2025). Commercial terms of service, effective 17 June 2025. https://www.anthropic.com/legal/commercial-terms
- Modal. Data processing agreement. https://modal.com/legal/dpa
- Modal. Security and privacy. https://modal.com/docs/guide/security
- Morris, J. X., Kuleshov, V., Shmatikov, V., & Rush, A. M. (2023). Text embeddings reveal (almost) as much as text. *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, 12448–12460. arXiv:2310.06816.
