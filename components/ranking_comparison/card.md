# Card: ranking comparison

**Purpose.** Analyses A2 and A3: rankings and selections by the AI and by the judges, and the test of agreement at the top and divergence near the cutoff.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses SciPy, NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Ties in the AI's scores at the cutoff are broken by entry code; the output records how many entries tie there.
- The bands hold few entries (ten at the top), so their intervals are wide.
- Ranks are computed once on all entries; the bootstrap resamples entries' rank differences, not the rankings.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `ranking_comparison`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `6c33921c79b65c82b4e09bb27b7845f87eb52b98d34c992cc11b185bb7044d5b`
- **Validation status:** provisional; population: The round 1 judging of the competition and the AI judges' answers, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6, scipy 1.18.1
- **Settings:** `{"bootstrap_reps": 2000, "cutoff_half_width": 10, "judges_per_entry": 3, "seed": 2019, "top_band": 10}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on simulated rankings | unit_tests |  | all pass | pass | tests/test_study_a.py |
<!-- END GENERATED FROM CONTRACT -->
