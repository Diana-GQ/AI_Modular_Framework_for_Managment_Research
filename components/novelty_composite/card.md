# Card: novelty composite

**Purpose.** The primary novelty measure: the mean of the three embedders' standardized novelty scores, more reliable than any one of them (Spearman-Brown reliability 0.70).

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Not validated against human ratings in this study; described, not tested.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `novelty_composite`, version 1.0.0, role aggregator, deterministic.
- **Configuration hash:** `55de030f5250145e66072bf2e1885cbac543ff7898975075e2f273cc1a5ffe5d`
- **Validation status:** provisional; population: The executive summaries of the competition, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6
- **Settings:** `{"embedders": ["embedder_bge_m3", "embedder_gte_modernbert", "embedder_qwen3"]}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests | unit_tests |  | all pass | pass | tests/test_phase5.py |
| The embedders agree | reliability | mean Spearman correlation between the embedders' novelty scores, and the composite's Spearman-Brown reliability | reported | mean correlation 0.43; composite reliability 0.70 | this component's output |
| Novelty agrees with human ratings of novelty | validity | correlation of the composite with human ratings of a random sample of summaries | not done in this study, which has no human coders; future work. Until then novelty is used descriptively and stays out of inference | not yet run | none yet |
<!-- END GENERATED FROM CONTRACT -->
