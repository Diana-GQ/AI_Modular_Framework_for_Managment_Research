# Card: novelty profile

**Purpose.** Describes, without testing, how the human and AI scores and advancement vary across fifths of the entries by novelty.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- A description only: novelty has no human validation, so no test is run.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `novelty_profile`, version 1.0.0, role aggregator, deterministic.
- **Configuration hash:** `45cfb1e8a6bb60b43fcefff23710b6afd75748769c7c5136ed4b0bace1e19068`
- **Validation status:** provisional; population: The judged entries of the competition, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6
- **Settings:** `{"bins": 5}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests | unit_tests |  | all pass | pass | tests/test_phase5.py |
<!-- END GENERATED FROM CONTRACT -->
