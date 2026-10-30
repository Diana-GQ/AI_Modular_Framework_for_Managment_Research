# Card: topics

**Purpose.** Clusters the summaries into topics, from one embedder's whitened vectors, and describes each topic by its most distinctive words.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses NumPy and SciPy (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- The embedders' topics agree only modestly (adjusted Rand index 0.20 to 0.34), so topics are descriptive.
- Distinctive words are filtered to keep names out: a word must appear in at least three summaries of the topic, must not be capitalized in most of its occurrences away from the start of a sentence, and must not be a word of a person's name, or a one-word term, in the private term list. The words of longer venture and institution names are left to the first two rules.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `topics`, version 1.0.0, role representer, deterministic.
- **Configuration hash:** `2baf4b9aec68ddf778d3795c61fbcd258cac966ae763284864793e60e981d3c7`
- **Validation status:** provisional; population: The executive summaries of the competition, 2019
- **Tools:** numpy 2.5.4, scipy 1.18.1
- **Settings:** `{"max_topics": 8, "min_documents": 3, "min_topics": 4, "prior": 1000, "top_words": 12, "whitening_dimensions": 8}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic vectors | unit_tests |  | all pass | pass | tests/test_phase5.py |
| The embedders find similar topics | agreement | adjusted Rand index between each pair of embedders' topics | reported; the settings that separated topics best at equal agreement were chosen | variants compared on 2019: whitening to 8 components gave mean silhouettes of 0.19 to 0.26 and adjusted Rand indices of 0.20 to 0.34; centring alone, 0.04 and 0.21 to 0.33; whitening to 64, under 0.02 and under 0.05 | the topic agreement component's output |
<!-- END GENERATED FROM CONTRACT -->
