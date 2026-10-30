# Card: synthetic summary

**Purpose.** Writes the synthetic competition's applications (design, B4): for each fictional venture, with the name and concept the synthetic concepts component invented, Claude Sonnet 5.5 invents a team, a one-line pitch, a description and a two-page executive summary whose strength and writing match the venture's hidden quality and quality of writing.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Calls Anthropic's API under the project's commercial terms.

**Data terms.** Each call sends the venture's simulated attributes, and nothing from the real records, to Anthropic's API from the project's paid account. Requests and responses are stored in the synthetic competition's store, but not published.

**How it asks.**
- The system prompt asks for invented material only: no real company, product, person or university, no contact details, and the founders' university called "our university".
- The venture's quality and quality of writing are given as words on five levels (`prompts.yaml`), and the summary must reflect them without stating them.
- The answer's form is enforced by structured outputs. A failed, refused or cut-off call raises an error, so nothing is stored and the next build asks again.

**Known failure modes.**
- An invented name or word may coincide with one in the real records. The synthetic stage checks every generated text against the real records' sensitive-term list, and writes again, under a new attempt number, any text that matches.
- The summaries follow the model's idea of a student executive summary, which is more uniform than real summaries; their layouts are plain.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `synthetic_summary`, version 1.0.0, role generator, stochastic.
- **Configuration hash:** `d8b4d784f9a555b1569766cc05065aec952b14b7db4d4f9a093cb76e39281941`
- **Validation status:** provisional; population: The synthetic competition
- **Model:** `{"id": "claude-sonnet-5-5", "provider": "Anthropic API"}`
- **Tools:** anthropic 1.13.0
- **Settings:** `{"effort": "high", "max_tokens": 6000, "thinking": {"type": "between_tools"}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests with a stand-in API client | unit_tests |  | all pass | pass | tests/test_synthetic.py |
| No real name enters the synthetic records | consistency | matches of the sensitive-term list of the real records in the generated texts | none | pass: no final text matches; 6 of the 40 summaries were written again once, after an attempt matched | synthetic/data/synthetic.json |
<!-- END GENERATED FROM CONTRACT -->
