# Card: embedding agreement

**Purpose.** Measures whether the three embedders see the same structure in the same texts, by correlating their pairwise similarities.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses SciPy and NumPy (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Computed on a random sample of 2,000 feedback texts, fixed by the seed, and on all summaries.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `embedding_agreement`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `f55b25729683f2a9184211861ade6b4120f01a065d575e09b0bdbb31816edda0`
- **Validation status:** provisional; population: The written feedback and summaries of round 1, 2019
- **Tools:** numpy 2.5.4, scipy 1.18.1
- **Settings:** `{"sample_size": 2000, "seed": 2019}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic vectors | unit_tests |  | all pass | pass | tests/test_study_a.py |
<!-- END GENERATED FROM CONTRACT -->
