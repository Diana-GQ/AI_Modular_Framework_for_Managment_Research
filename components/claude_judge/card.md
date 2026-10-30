# Card: Claude judge

**Purpose.** Generates the main AI evaluations of Study A: for each judged executive summary, Claude Sonnet 5.5 answers the judges' ten questions (design, Section 2.1), one question per call, five times each.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Calls Anthropic's API under the project's commercial terms; outputs belong to the project under those terms.

**Data terms.** Each call sends one summary's text and one question to Anthropic's API, from the project's paid account with data sharing off (design, Section 7). Nothing else leaves project machines. Requests and responses are stored in `data/store/`.

**How it asks.**
- The system prompt is the authors' (design, Section 2.1). The user message is "Business plan text:", the summary, and "Question:" with the question.
- The answer's form is enforced by Anthropic's structured outputs: `{"response": text}` for written questions, `{"score": 1-10}` for score questions.
- Written answers are long: in the pilot, their medians ran from about 450 to 670 words by question, against 40 to 60 words for the human judges. The length limit is 8,192 tokens.
- Thinking is off (`thinking: between_tools` at `high` effort, the lowest setting this model accepts).
- The summary's part of the message is marked for caching, so the 50 calls on a summary pay full price for it once.
- No fallbacks to other models are requested; an answer reported as coming from another model stops the run.

**What cannot be fixed.** The model accepts only its default sampling settings, and the API has no seed. Runs are separate draws: they are reproduced from their stored outputs, not re-executed exactly.

**Known failure modes.**
- Refusals: recorded with status `refusal`, counted as missing answers, and reported.
- Answers cut off at the length limit: status `max_tokens`, counted as missing.
- Q10 refers to an investment interest rating that, asked separately, the model has not given. In the pilot, about one answer in six to Q10 states a rating of its own.
- The model may be retired; its stored outputs remain, and drift is measured while it is offered.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `claude_judge`, version 1.0.0, role judge, stochastic.
- **Configuration hash:** `1a53fe88c1da14e405f6b5e7c4e14274f05c324d143c4b9d7f2294cc8cdc4531`
- **Validation status:** validated; population: Executive summaries of the competition's round 1, 2019
- **Model:** `{"id": "claude-sonnet-5-5", "provider": "Anthropic API"}`
- **Tools:** anthropic 1.13.0
- **Settings:** `{"effort": "high", "max_tokens": {"score": 64, "written": 8192}, "thinking": {"type": "between_tools"}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests with a stand-in API client | unit_tests |  | all pass | pass | tests/test_judges.py, tests/test_models.py |
| Every answer parses, and none is refused or cut off | consistency | share of calls with status ok | 1.0, or every exception explained | pass: pilot 1,000 of 1,000 (configuration 837226764ae0); full run 6,700 of 6,700 (configuration 1a53fe88c1da) | data/reports/2019_pilot.json, data/reports/2019_full_run.json |
| Consistency across the five runs | reliability | intraclass correlation of the five runs' scores, ICC(1), for each score question | reported; no threshold before Study A | full run, 134 summaries: ICC(1) from 0.92 to 0.95 across the five score questions, 0.98 for the weighted score (pilot: 0.92 to 0.95) | data/reports/2019_pilot.json; the score agreement component's output for this judge (Study A, A1) |
<!-- END GENERATED FROM CONTRACT -->
