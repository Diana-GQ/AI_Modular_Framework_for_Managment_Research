# Documentation

[`design.md`](design.md) describes the study that illustrates the framework: the data, the AI evaluations, the components, Study A (the illustration), Study B (the reproducibility audit) and the safeguards. The [README](../README.md#the-framework) summarizes the framework.

## How the code cites these documents

Docstrings, comments and the reports that the pipeline writes cite the documents in short form. Most citations name a section of the design or the framework. Some name the section of the framework under its working title, the proposal. Others name the phase or task of the work plan in which a step was built.

These citations stay as written. Many sit in files that the components' contracts pin, and a pinned file is part of its component's configuration hash (framework, Section 3). Editing a comment there would change the hash, and with it the keys of the stored outputs. This table resolves every form.

| Citation | Where to read |
|---|---|
| *(design, Section N)*, *(the design's Section N)*, *(design, A1)* to *(design, A6)*, *(design, B1)* to *(design, B5)* | [`design.md`](design.md), the same section or analysis |
| *(framework, Section N)*, *(proposal, Section 4.2)* and *(proposal, Section 4.4)* | The framework's full description, not yet in this repository. The [README](../README.md#the-framework) summarizes it |
| *the plan's Section 3 (Later: human validation of the measures)* | [`design.md`](design.md), Section 3, "Human validation of the measures" |
| *(plan, Phase N)*, *(plan, task N.N)*, *task N.N* | The table below |

## The phases and tasks of the work

The pipeline was built in phases. Each task below built a part of it, and the code and reports name the task.

| Phase | Task | What it built | Where | Command |
|---|---|---|---|---|
| 2. The 2019 records | 2.2 | The text of every executive summary, with page and word counts, and the extraction checks | `components/text_extractor/`, `pipeline/stages/extract.py` | `pipeline.stages.extract <year>` |
| | 2.3 | A random code for every entry and judge; the key is kept apart, in `data/private/` | `pipeline/pseudonyms.py`, `pipeline/stages/pseudonymize.py` | `pipeline.stages.pseudonymize <year>` |
| | 2.4 | The four analysis tables (design, Section 1.3), and their sensitive-term check | `components/records_tables/`, `pipeline/stages/tables.py` | `pipeline.stages.tables <year>` |
| | 2.5 | A profile of the records, in counts only | `pipeline/stages/profile.py` | `pipeline.stages.profile <year>` |
| 3. The AI evaluations | 3.3 | The pilot: both AI judges on 20 summaries, and the open-weight judge's determinism test on its 200 prompts | `components/claude_judge/`, `components/qwen_judge/`, `pipeline/stages/judge.py` | `pipeline.stages.judge pilot <year>`, `determinism <year>`, `report <year>` |
| | 3.4 | The full run: both AI judges on every judged summary, ten questions, five runs | the same | `pipeline.stages.judge full <year>`, `full-report <year>` |
| 4. Study A, first pass | 4.1 | The human benchmark: how much the judges agree | `components/human_benchmark/` | `pipeline.stages.study_a benchmark <year>` |
| | 4.2 | A1: the AI judges' scores against the judges', consistency across runs and halo | `components/score_agreement/` | `pipeline.stages.study_a agreement <year>` |
| | 4.3 | A2 and A3: rankings, selections and the cutoff | `components/ranking_comparison/` | `pipeline.stages.study_a rankings <year>` |
| | 4.4 | A4: the written feedback, through three embedders and through text analysis | the three embedders, `pipeline/modal_embed.py`, `components/feedback_comparison/`, `components/embedding_agreement/`, `components/feedback_text/` | `pipeline.stages.study_a embed <year>`, `embed-check <year>`, `feedback <year>` |
| 5. Measures and Study A, second pass | 5.1 | The measures: the style and language profile, novelty, topics and the ventures' characteristics | `components/style_profiler/`, `novelty/`, `novelty_composite/`, `topics/`, `topic_agreement/`, `venture_characteristics/` | `pipeline.stages.study_a measures <year>` |
| | 5.2 | Checks of the measures without human coders: similarities against the teams' own categories, and agreement across embedders | `components/similarity_known_groups/` | `pipeline.stages.study_a report <year>` |
| | 5.3 | A5: what explains the human scores, the AI scores and their differences; novelty described | `components/score_explanation/`, `components/novelty_profile/` | `pipeline.stages.study_a explain <year>` |
| | 5.5 | The findings to test on further years, listed in the Study A report | `pipeline/stages/study_a_report.py` | `pipeline.stages.study_a report <year>` |
| | 5.6 | The frozen pipeline: every component's version and configuration hash | `components/frozen.json`, `pipeline/freeze.py` | `pipeline.freeze check` |
| 6. Study B | 6.1 | B1: the analysis rebuilt in a fresh copy of the repository | `pipeline/stages/study_b.py` | `pipeline.stages.study_b reproduce <year>` or `synthetic` |
| | 6.4 | B4: the synthetic competition, and the whole pipeline run on it | `components/synthetic_*/`, `pipeline/stages/synthetic.py`, `synthetic/` | `pipeline.stages.synthetic build`, `run` |
| 7. Further years | 7.3 | A6: change over the editions since 2019 | not yet built | |

Of Study B (design, Section 5), B1 and B4 are built. B2 is tested so far on the pilot only: the open-weight judge's determinism test (task 3.3) and the embedders' re-execution (task 4.4). B3, B5 and the outside researcher's reproduction, B4's test, are not yet done.

Each command runs as `uv run python -m <command>`. Phase 1 built the framework itself (`pipeline/`) and its first component, `weighted_score`, which A1 to A5 use. Phases 4 and 5 are Study A's two passes over a year's records. `pipeline.stages.study_a report <year>` runs every analysis of Study A, reusing what is stored, and writes its report.
