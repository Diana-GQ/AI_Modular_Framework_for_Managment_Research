# Card: score explanation

**Purpose.** Analysis A5: which features of the summaries' form and the ventures' substance explain the human and AI scores, where they diverge, and who advanced.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses statsmodels, NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Exploratory: many coefficients on 134 entries; patterns to test on further years.
- Novelty is not among the features, since it has no human validation.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `score_explanation`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `421b67a38799a5b143f13069538115d616014d251dd5ce63c1f5bde862139694`
- **Validation status:** provisional; population: The judged entries of the competition, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6, statsmodels 0.15.0
- **Settings:** `{"bootstrap_reps": 2000, "form": ["log_words", "flesch_reading_ease", "hedges_per_100_words", "boosters_per_100_words", "numbers_per_100_words", "we_per_100_words"], "seed": 2019, "substance": ["internet_consumer_tech", "product_software_app", "product_physical_product", "product_data_analytics", "product_service", "milestones_reached", "milestone_first_client_has_paid", "milestone_funding_raised", "entity_formed", "has_website"]}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on simulated data | unit_tests |  | all pass | pass | tests/test_phase5.py |
<!-- END GENERATED FROM CONTRACT -->
