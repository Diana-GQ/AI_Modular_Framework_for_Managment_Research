# Card: synthetic feedback

**Purpose.** Writes the synthetic judges' comments (design, B4): for each evaluation of the synthetic competition, Claude Sonnet 5.5 writes, as the fictional judge with its persona, the comments on the judging form's six written questions, consistent with the scores the simulation gave.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Calls Anthropic's API under the project's commercial terms.

**Data terms.** Each call sends a synthetic summary, the judge's persona and the simulated scores, and nothing from the real records, to Anthropic's API from the project's paid account. Requests and responses are stored in the synthetic competition's store, but not published.

**How it asks.**
- The judge writes in its own voice, briefly, and without stating its scores; most comments run 15 to 70 words, as most judges' do, and the optional comment on the concept score is left empty about one time in four.
- The answer's form is enforced by structured outputs. A failed, refused or cut-off call raises an error, so nothing is stored and the next build asks again.

**Known failure modes.** One model writes every judge's comments, so they vary less in style than real judges' do, despite the personas. Study A's comparisons of human and AI feedback on the synthetic competition therefore compare two kinds of machine writing.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `synthetic_feedback`, version 1.0.0, role generator, stochastic.
- **Configuration hash:** `dadbcccb5f9d0dd07c2d06488df8fa9a3c0e63614bf908bdd0a26b9ba045b891`
- **Validation status:** provisional; population: The synthetic competition
- **Model:** `{"id": "claude-sonnet-5-5", "provider": "Anthropic API"}`
- **Tools:** anthropic 1.13.0
- **Settings:** `{"effort": "high", "max_tokens": 2000, "thinking": {"type": "between_tools"}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests with a stand-in API client | unit_tests |  | all pass | pass | tests/test_synthetic.py |
| No real name enters the synthetic records | consistency | matches of the sensitive-term list of the real records in the generated texts | none | pass: no final text matches; 3 of the 120 sets of comments were written again once, after an attempt matched | synthetic/data/synthetic.json |
<!-- END GENERATED FROM CONTRACT -->
