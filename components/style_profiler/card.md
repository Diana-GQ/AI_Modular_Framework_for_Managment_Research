# Card: style and language profiler

**Purpose.** Measures the form of each summary for A5: length, readability, hedging, boosting, quantification and the team's voice. Code only.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses textstat (MIT) and pyphen (LGPL/GPL/MPL).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Readability formulas were built for general prose, not business plans with tables and bullet points.
- Hedges and boosters are dictionary counts (Hyland 2005), blind to context.
- Word files have no page count, so the page limit is checked for PDFs only.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `style_profiler`, version 1.0.0, role representer, deterministic.
- **Configuration hash:** `19cc68ed388cfe79d853ae9f20119b5489f57924cdd390ca1c582146d6c4887d`
- **Validation status:** validated; population: The executive summaries of the competition, 2019
- **Tools:** pyphen 0.18.1, textstat 0.7.13
- **Settings:** `{"boosters": ["actually", "always", "believe", "believed", "believes", "certain", "certainly", "clear", "clearly", "conclusively", "decidedly", "definite", "definitely", "demonstrate", "demonstrated", "demonstrates", "doubtless", "establish", "established", "evident", "evidently", "find", "finds", "found", "indeed", "indisputable", "indisputably", "know", "known", "must", "never", "obvious", "obviously", "prove", "proved", "proves", "proven", "realize", "realized", "really", "show", "showed", "shown", "shows", "sure", "surely", "truly", "undeniable", "undeniably", "undoubtedly", "beyond doubt", "in fact", "no doubt", "of course", "without doubt"], "hedges": ["about", "almost", "apparent", "apparently", "appear", "appeared", "appears", "approximately", "argue", "argued", "argues", "around", "assume", "assumed", "broadly", "claim", "claimed", "claims", "could", "doubt", "doubtful", "essentially", "estimate", "estimated", "fairly", "feel", "feels", "felt", "frequently", "generally", "guess", "indicate", "indicated", "indicates", "largely", "likely", "mainly", "may", "maybe", "might", "mostly", "often", "ought", "perhaps", "plausible", "plausibly", "possible", "possibly", "presumably", "probable", "probably", "quite", "rather", "relatively", "roughly", "seem", "seems", "seemed", "should", "sometimes", "somewhat", "suggest", "suggested", "suggests", "suppose", "supposed", "suspect", "tend", "tended", "tends", "typical", "typically", "uncertain", "unclear", "unlikely", "usually", "would", "in general", "in most cases", "on the whole", "to some extent", "it seems", "i think", "i believe", "in my view", "in my opinion"], "page_limit": 2}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic texts | unit_tests |  | all pass | pass | tests/test_phase5.py |
<!-- END GENERATED FROM CONTRACT -->
