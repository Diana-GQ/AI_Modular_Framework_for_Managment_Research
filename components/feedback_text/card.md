# Card: feedback text analysis

**Purpose.** Analysis A4 through text analysis: length, hedging and tone of human and AI feedback, and the words that most distinguish them, by question.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses vaderSentiment (MIT), NumPy and pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Hedging and tone are dictionary counts, not validated for evaluation feedback. A5's measures of the summaries' form come from the style and language profiler (`style_profiler`), not from this component.
- Distinguishing words are filtered to keep names out: a word must appear on at least five entries, must not be capitalized in most of its occurrences away from the start of a sentence, and must not be a word of a person's name, or a one-word term, in the private term list. The words of longer venture and institution names are left to the first two rules.

**Version history.**
- 1.0.0: first version.
- 1.0.1: ties between equally distinguishing words are broken alphabetically. Before, they followed the order of a set, which changes from one run to the next (found by B1).

**Errata.** In version 1.0.0, words with equal scores could appear in a different order from one run to the next. On 2019 this affected only places 13 and 14 of one list of 15, below the ten that the Study A report shows.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `feedback_text`, version 1.0.1, role validator, deterministic.
- **Configuration hash:** `13999668c3f8a9c43afe4eeddb037fa49ee22b4c4c99e19e489168b5e406d603`
- **Validation status:** provisional; population: The written feedback of round 1, 2019, human and AI
- **Tools:** numpy 2.5.4, pandas 3.0.6, vaderSentiment 3.3.2
- **Settings:** `{"ai_sources": ["claude_judge", "qwen_judge"], "hedges": ["about", "almost", "apparent", "apparently", "appear", "appeared", "appears", "approximately", "argue", "argued", "argues", "around", "assume", "assumed", "broadly", "claim", "claimed", "claims", "could", "doubt", "doubtful", "essentially", "estimate", "estimated", "fairly", "feel", "feels", "felt", "frequently", "generally", "guess", "indicate", "indicated", "indicates", "largely", "likely", "mainly", "may", "maybe", "might", "mostly", "often", "ought", "perhaps", "plausible", "plausibly", "possible", "possibly", "presumably", "probable", "probably", "quite", "rather", "relatively", "roughly", "seem", "seems", "seemed", "should", "sometimes", "somewhat", "suggest", "suggested", "suggests", "suppose", "supposed", "suspect", "tend", "tended", "tends", "typical", "typically", "uncertain", "unclear", "unlikely", "usually", "would", "in general", "in most cases", "on the whole", "to some extent", "it seems", "i think", "i believe", "in my view", "in my opinion"], "min_entries": 5, "prior": 1000, "questions": ["Q1", "Q3", "Q5", "Q8", "Q10"], "top_words": 15}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic texts | unit_tests |  | all pass | pass | tests/test_study_a.py |
<!-- END GENERATED FROM CONTRACT -->
