# The synthetic competition

The competition's records may not be published or shared, so the repository carries a synthetic competition instead (design, B4). It has the same files and layout as a real edition, under a fictional year, 2000, and the whole pipeline runs on it, so that anyone can rerun every step and check the results.

## What is invented, and how

| Part | Made by | How |
|---|---|---|
| 40 ventures, their answers to the application form, and a hidden quality and quality of writing; and 4 applications never submitted, as in a real edition | `components/synthetic_competition` | A simulation with a fixed seed. The form's answers follow the shares of the 2019 answers, rounded. |
| 15 judges, three per venture, and their scores on the five criteria | `components/synthetic_competition` | Each score adds the venture's quality (its quality of writing, for the written work), the judge's severity and a reaction to the venture. Their shares of the variance, and the judges' halo, are rounded from those measured on 2019. The top 30% by mean weighted score advance. |
| Each venture's name and concept | `components/synthetic_concepts` | Claude Sonnet 5.5 invents all 40 in one call, each fitting the venture's form answers, so that the ventures differ from one another. |
| Each venture's team, pitch, description and two-page executive summary | `components/synthetic_summary` | Claude Sonnet 5.5 writes them for the venture's name and concept, to match its hidden quality and quality of writing without stating either. |
| Each judge's comments on the six written questions | `components/synthetic_feedback` | Claude Sonnet 5.5 writes them as the judge, with the judge's persona and consistent with the judge's scores. |

Only rounded aggregates of the 2019 records enter the simulation; no record does. Every generated text is checked against the sensitive-term list of the real records, and a text that matches is written again under a new attempt number; `data/synthetic.json` records the outcome.

## Files

```
data/
  synthetic.json                 how and when the competition was built, and the checks it passed
  raw/2000/2000 R1.xlsx          the export: the applications sheet and the round 1 judging sheet
  raw/2000/R1/PDF, R1/Word       the executive summaries: 35 PDF and 5 Word files
  manifests/2000_documents.csv   the inventory of the summaries, with checksums
  private/code_key.csv           the codes of the fictional entries and judges
  private/sensitive_terms.tsv    the fictional names, which the text measures leave out
  reports/                       the pipeline's reports, including Study A's report on the synthetic competition
  store/                         the components' stored outputs, with their provenance records
  tables/2000/                   the four analysis tables, and the AI judges' answers (evaluations_ai)
```

The published store holds the outputs of every component except the generators. From the AI judges' and embedders' outputs, every other result can be recomputed without calling an AI model, and compared with the one stored. The generators' outputs are not published: the files they wrote are here, and their earlier attempts include texts that matched the real records' term list. In the published provenance records, the person who ran each step is given as "the authors".

## Commands

```
uv run python -m pipeline.stages.study_b reproduce synthetic   # every result recomputed from the AI outputs, and compared
uv run python -m pipeline.stages.synthetic build               # generate the competition (calls Anthropic's API)
uv run python -m pipeline.stages.synthetic run                 # run the pipeline on it (calls Anthropic's API and Modal)
```

`reproduce` calls no model. It copies the repository into a new folder with a new environment, leaving out `data/store/` and `data/tables/`. It then brings in the AI judges' and embedders' stored outputs, computes every other output again, and compares each with the one in `data/`. Its findings go to `data/reports/2000_b1_reproduction.json`. `run` calls the models for any answer not yet stored, and re-executes the embedders in new containers to check that they give identical vectors. With the published store in place, it therefore calls only the embedders; for new answers from the AI judges, move `data/store/` and `data/tables/` out of the repository first.

`build` generates a new competition: Claude Sonnet 5.5 invents new ventures, summaries and comments, and the build replaces the files in `data/raw/2000/`, the inventory, `data/private/sensitive_terms.tsv` and `data/synthetic.json`. The published store and tables then no longer match the files. The check against the real records' term list runs only where that list exists, on the authors' machines; elsewhere `data/synthetic.json` records it as not run.

The pipeline's stages also run one by one on the synthetic competition, with `COMPAI_DATA` set to the folder `synthetic/data` and the year 2000:

```
COMPAI_DATA=$PWD/synthetic/data uv run python -m pipeline.stages.study_a report 2000
```
