# Card: novelty

**Purpose.** Measures each summary's distinctiveness from the year's other summaries, from one embedder's vectors, and stores the similarities it rests on.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses NumPy (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Semantic distance is a limited measure of novelty (Organisciak et al. 2023), and the three embedders agree only moderately (mean Spearman 0.43).
- No human ratings of novelty exist in this study: it is described, not tested, and the methodological check keeps it out of inference.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `novelty`, version 1.0.0, role representer, deterministic.
- **Configuration hash:** `b33baee1a7c5cdd3c86b25c1bcd9eb5aa08177122448729c7eb31fd5e57b0430`
- **Validation status:** provisional; population: The executive summaries of the competition, 2019
- **Tools:** numpy 2.5.4
- **Settings:** `{"nearest_neighbours": 5}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic vectors | unit_tests |  | all pass | pass | tests/test_phase5.py |
| Agreement across the three embedders | agreement | Spearman correlation between embedders' novelty scores | reported; the variant that agreed best was chosen before coding | mean 0.43 (0.39 to 0.48) for the five nearest neighbours on normalized vectors; variants with centring or whitening agreed less (0.21 to 0.38) | the novelty composite component's output |
| The similarities track the teams' own categories (known groups) | validity | mean similarity of pairs whose teams chose at least two of the same fields minus that of pairs with nothing in common, 95% interval from resampling summaries | the interval excludes zero, for each embedder (set on 2026-10-13, before the check was run) | pass for all three embedders: standardized differences 0.83 to 0.90; Spearman correlation with category overlap 0.30 to 0.34 | the similarity known-groups component's output |
| Novelty agrees with human ratings of novelty | validity | correlation with human ratings of a random sample of summaries | not done in this study, which has no human coders; future work. Until then novelty is used descriptively and stays out of inference | not yet run | none yet |
<!-- END GENERATED FROM CONTRACT -->
