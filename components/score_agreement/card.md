# Card: score agreement

**Purpose.** Analysis A1: how closely an AI judge's scores agree with the human judges', against the benchmark of one judge against the other two; the AI's consistency across runs; and halo.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses SciPy, NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- The AI's mean of five runs is more reliable than one judge's score; one AI run is reported beside it.
- Pooling the three held-out judges counts each entry three times; the intervals come from resampling entries, which accounts for it.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `score_agreement`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `949c5d14c563286de0d5b9f473da14761015b050e2dc5f0388f160a111fec705`
- **Validation status:** provisional; population: The round 1 judging of the competition and the AI judges' answers, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6, scipy 1.18.1
- **Settings:** `{"bootstrap_reps": 2000, "criteria": {"Q2": "concept", "Q4": "business_model", "Q6": "market", "Q7": "written_work", "Q9": "investor_interest"}, "seed": 2019}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on simulated scores | unit_tests |  | all pass | pass | tests/test_study_a.py |
<!-- END GENERATED FROM CONTRACT -->
