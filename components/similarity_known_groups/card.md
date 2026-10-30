# Card: similarity known groups

**Purpose.** Checks the embedding similarities against the teams' own categories on the application form, in place of human similarity ratings, which this study does not have.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses NumPy and SciPy (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- The categories are coarse and self-reported: the check shows that similarity tracks what the ventures are about, not how alike their ideas are.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `similarity_known_groups`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `8a8118be82dcfe270a25704804ae3d17a99c882182866f5a75b8f4c431b4697d`
- **Validation status:** provisional; population: The judged summaries of the competition, 2019
- **Tools:** numpy 2.5.4, scipy 1.18.1
- **Settings:** `{"bootstrap_reps": 2000, "same_fields_min": 2, "seed": 2019}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic similarities | unit_tests |  | all pass | pass | tests/test_phase5.py |
| Similarity is higher within the teams' shared fields | validity | mean similarity of pairs sharing at least two fields minus that of pairs with nothing in common, 95% interval from resampling summaries | the interval excludes zero, for each embedder (set on 2026-10-13, before the check was run) | pass for all three embedders: differences of +0.036 to +0.040, every 95% interval above zero (standardized differences 0.83 to 0.90) | this component's output; data/reports/2019_study_a_report.md, Section 5 |
<!-- END GENERATED FROM CONTRACT -->
