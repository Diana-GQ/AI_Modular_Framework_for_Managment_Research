# Card: human benchmark

**Purpose.** Measures how much the human judges agree with one another, the benchmark against which Study A reads the AI judges (design, A1).

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses statsmodels (BSD), SciPy (BSD), NumPy (BSD) and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- The judges' errors are not separated from their reactions to particular entries, because each judge scores an entry once: the residual holds pattern noise and any other error.
- Judges were assigned to entries at random (organizers), so judge severity is not confounded with the quality of the entries a judge saw.

**Version history.**
- 1.0.0: first version.
- 1.1.0: the mixed model is fitted with Powell's search refined by BFGS, keeping the better fit, instead of L-BFGS alone. A variance estimated at essentially zero is set to zero and the others are fitted again. The outputs are reproduced to within a relative 1e-5 (the contract's `reproduced_within`), since they come from an optimizer.

**Errata.** Version 1.0.0's L-BFGS fit could stop at the boundary, with a variance of zero, short of the best fit. B1 found this on the synthetic competition's market scores, whose best fit puts 5% of the variance between entries, not 0%. On 2019 the two fits agree to the precision the Study A report shows. Version 1.0.0's outputs also varied from run to run in their last digits.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `human_benchmark`, version 1.1.0, role validator, deterministic.
- **Configuration hash:** `b8e6843ee4d361dad62c432553b51ec535a59fbb99a261a201ca38342d6402ad`
- **Validation status:** provisional; population: The round 1 judging of the competition, 2019
- **Tools:** numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, statsmodels 0.15.0
- **Settings:** `{"criteria": {"Q2": "concept", "Q4": "business_model", "Q6": "market", "Q7": "written_work", "Q9": "investor_interest"}, "estimation": "REML, entries and judges as crossed random effects; Powell's search refined by BFGS, keeping the better fit", "judges_per_entry": 3}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently
- **Reproduced within:** a relative difference of 1e-05; the outputs come from a numerical optimizer

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on simulated scores with known variance components | unit_tests |  | all pass | pass | tests/test_study_a.py |
<!-- END GENERATED FROM CONTRACT -->
