# Card: synthetic concepts

**Purpose.** Invents the synthetic competition's ventures (design, B4): in one call, Claude Sonnet 5.5 gives every fictional venture a name and a one-sentence concept that fits its answers on the application form. Asked one venture at a time, the model gives many ventures the same few ideas and name parts. Asked for all of them at once, it can make them differ, as a real competition's entries do.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Calls Anthropic's API under the project's commercial terms.

**Data terms.** The call sends the ventures' simulated form answers, and nothing from the real records, to Anthropic's API from the project's paid account. The request and response are stored in the synthetic competition's store, but not published.

**How it asks.**
- The prompt asks for ventures spread across many industries, customers and problems, with no two sharing a problem, customers or a part of their names. It also lists name parts that startups overuse.
- The answer's form is enforced by structured outputs. A failed call, or concepts that do not match the ventures one to one, raises an error, so nothing is stored.

**Known failure modes.** The model's idea of a varied competition is still its own. Its ventures may lean towards the kinds of startups it has seen described most often.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `synthetic_concepts`, version 1.0.0, role generator, stochastic.
- **Configuration hash:** `f17c00b01f6e7fb1acf84cc413933cae730dd3e42bf4db3aa09a293847c9e235`
- **Validation status:** provisional; population: The synthetic competition
- **Model:** `{"id": "claude-sonnet-5-5", "provider": "Anthropic API"}`
- **Tools:** anthropic 1.13.0
- **Settings:** `{"effort": "high", "max_tokens": 8000, "thinking": {"type": "between_tools"}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests with a stand-in API client | unit_tests |  | all pass | pass | tests/test_synthetic.py |
| No real name enters the synthetic records | consistency | matches of the sensitive-term list of the real records in the generated texts | none | pass: no final text matches; no concept was written again | synthetic/data/synthetic.json |
<!-- END GENERATED FROM CONTRACT -->
