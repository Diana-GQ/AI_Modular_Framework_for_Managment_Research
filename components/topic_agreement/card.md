# Card: topic agreement

**Purpose.** Measures how far the embedders' topics agree, by the adjusted Rand index.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). No dependencies beyond Python.

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- The index treats every disagreement alike, whatever the topics' sizes.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `topic_agreement`, version 1.0.0, role validator, deterministic.
- **Configuration hash:** `f7929ecb666b3173799a54b992fb3a0910453d4d8a180cf23de606bec4e8d297`
- **Validation status:** provisional; population: The executive summaries of the competition, 2019
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests | unit_tests |  | all pass | pass | tests/test_phase5.py |
<!-- END GENERATED FROM CONTRACT -->
