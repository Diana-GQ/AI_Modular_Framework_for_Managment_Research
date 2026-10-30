# Card: weighted score

**Purpose.** Computes the competition's weighted score of one evaluation, the quantity by which entries are ranked: the mean of an entry's three weighted scores.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence).

**Data terms.** Runs locally on scores; sends nothing to any service.

**Known failure modes.** None known. The contract checks that the five scores are present and that the weighted score lies between 1 and 10; it does not check each score's range.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `weighted_score`, version 1.0.0, role aggregator, deterministic.
- **Configuration hash:** `7bb849928de872ebd0624030098155fba836cf8d3e06a38e08072f8625075376`
- **Validation status:** validated; population: Round 1 evaluations of the competition's executive summaries
- **Settings:** `{"weights": {"business_model": 0.2, "concept": 0.2, "investor_interest": 0.3, "market": 0.2, "written_work": 0.1}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Formula unit tests | unit_tests |  | all pass | pass | tests/test_weighted_score.py |
| Agreement with the weighted average recorded in the judging sheet | validity | maximum absolute difference | below 1e-6 | pass: no difference on the 405 evaluations of 2019 | data/reports/2019_profile.json (pipeline/stages/profile.py) |
<!-- END GENERATED FROM CONTRACT -->
