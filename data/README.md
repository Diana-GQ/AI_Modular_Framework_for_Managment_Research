# Data

This folder holds the competition's records, and everything the pipeline derives from them, on the authors' machines. Git ignores everything in it except this file. Under the organizers' terms, the summaries, the comments and data derived from them, including AI outputs and embeddings, may not be published or shared (design, Section 1.5). The repository carries a synthetic competition instead, in [`synthetic/`](../synthetic/README.md).

The layout:

```
data/
  raw/<year>/         exact copies of the sources: the export workbook and the executive summaries
  manifests/          the inventory of each year's documents, with checksums
  private/            restricted: the key that links codes to identities, the list of identifying terms, and the phrases the check passes over
  tables/<year>/      the four analysis tables and the AI judges' answers, with codes in place of identities (design, Section 1.3)
  store/              the components' stored outputs and provenance records (framework, Section 5)
  reports/            the pipeline's checks and reports, in counts, statistics and codes only
```

The synthetic competition has the same layout, in `synthetic/data/`. Its build ([`pipeline/stages/synthetic.py`](../pipeline/stages/synthetic.py)) writes the inventory of documents in the format the pipeline reads; the authors' script that builds it from the competition platform's export is specific to that platform and is not part of this repository. The variable `COMPAI_DATA` points the pipeline at another data folder ([`pipeline/paths.py`](../pipeline/paths.py)); the tests use it to write to a temporary folder.

The contracts' validated sections cite their evidence on 2019 by its path in this folder, such as `data/reports/2019_full_run.json`. Those files are not published. `synthetic/data/reports/` holds the corresponding reports for the synthetic competition, except the full determinism test, for which it has a shorter precheck, and the spot check of extracted texts.
