# Card: feedback comparison

**Purpose.** Analysis A4 through embeddings, for one embedder: whether AI and human feedback discuss the same issues, how alike each source's feedback is across entries, and how well feedback fits its own summary.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Length moves embeddings, and the AI judges write many times more than the judges; specificity (same entry minus different entries) is built to be robust to it, but raw similarities are not.
- The embedders have no validation against human similarity ratings; that validation is future work (design, Section 3).

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `feedback_comparison`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `0f150cecba495ee9c4f0783e4dec18032adff4ece81028dfb2a642d667ac5f9f`
- **Validation status:** provisional; population: The written feedback and summaries of round 1, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6
- **Settings:** `{"questions": ["Q1", "Q3", "Q5", "Q8", "Q10"], "sources": ["human", "claude_judge", "qwen_judge"]}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic vectors | unit_tests |  | all pass | pass | tests/test_study_a.py |
| Findings hold across the three embedders | consistency | same direction of each comparison for every embedder | reported for each finding | pass: each of the three comparisons reported has the same direction for all three embedders | data/reports/2019_study_a_report.md, Section 4 |
<!-- END GENERATED FROM CONTRACT -->
