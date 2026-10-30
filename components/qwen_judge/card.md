# Card: open-weight judge

**Purpose.** Generates the re-executable AI evaluations: the same ten questions as the Claude judge, answered by an open-weight model whose every run can be repeated exactly (design, Section 2.2).

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). The model, Qwen3-8B, is under the Apache-2.0 licence; vLLM is under the Apache-2.0 licence.

**Data terms.** Each batch sends summaries' texts and questions to a GPU container rented from Modal, under the project's paid account (design, Section 7). The container exists only while a run lasts, has no public endpoint, and writes no document text to its logs.

**How it asks.**
- The same system prompt, user message and questions as the Claude judge (`components/shared/judge_prompts.yaml`), in the model's chat template, with thinking switched off.
- A score answer is held by vLLM's structured outputs to the pattern `{"score": N}`, N from 1 to 10, with no room for stray whitespace.
- A written answer is plain text. In the pilot, written answers held to a JSON object sometimes stopped at the first line break, which JSON text cannot contain, and filled the length limit with blank space (25 of the first 250); plain text avoids this.
- Sampling follows the model's recommended settings for answers without thinking (temperature 0.7, top-p 0.8, top-k 20), with watermarking off. Run r uses seed r.

**What makes it re-executable.**
- The model's commit, the engine's container image (by digest) and the GPU type are pinned, and the component checks that the deployment matches its contract before it runs.
- vLLM runs in batch-invariant mode with prefix caching off, so an answer does not depend on which other requests share its batch.
- Identical outputs are guaranteed only on the same hardware and engine version; the determinism test checks them before each experiment.

**Known failure modes.**
- Answers cut off at the length limit (8,192 tokens): status `max_tokens`, counted as missing.
- An 8-billion-parameter model is weaker than Claude; its answers are a re-executable counterpart, not a second opinion of equal standing.
- Batch-invariant mode is in beta in vLLM 0.30.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `qwen_judge`, version 1.0.0, role judge, stochastic.
- **Configuration hash:** `08616c590e58ea4ec4e845164dbe2368e6af002e41c7733a2bf62dd145211544`
- **Validation status:** validated; population: Executive summaries of the competition's round 1, 2019
- **Model:** `{"engine": "vLLM 0.30.0, batch-invariant mode, prefix caching off, bfloat16, context of 16,384 tokens, structured outputs by xgrammar", "gpu": "H100!", "id": "Qwen/Qwen3-8B", "image": "vllm/vllm-openai:v0.30.0@sha256:8a69ffad015f138d7170c4ddc429e230a3bc1c1719f67e14324749df200a4b90", "licence": "Apache-2.0", "provider": "Modal", "revision": "b968826d9c46dd6066d109eabc6255188de91218"}`
- **Tools:** modal 1.6.1
- **Settings:** `{"max_tokens": {"score": 64, "written": 8192}, "sampling": {"min_p": 0.0, "presence_penalty": 0.0, "temperature": 0.7, "top_k": 20, "top_p": 0.8, "watermarking": false}, "seeds": [1, 2, 3, 4, 5], "structured_outputs": {"score": {"regex": "\\{\"score\": (10|[1-9])\\}"}, "written": null}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests with a stand-in deployment | unit_tests |  | all pass | pass | tests/test_judges.py |
| Re-execution gives identical outputs | determinism | share of 200 prompts whose output tokens are identical when sent one at a time, in one batch, in a shuffled batch, in the pilot's larger batches, and in a new container | 1.0 | pass: in the pilot (configuration 724ffb3a6a2d), 200 of 200 identical in every mode, across three containers; in the full run (configuration 08616c590e58), the 200 again before the run, and all 1,000 of the pilot's calls within it | data/reports/2019_determinism.json, data/reports/2019_determinism_precheck.json, data/reports/2019_full_run.json |
| Every answer parses, and none is cut off | consistency | share of calls with status ok | 1.0, or every exception explained | pass: pilot 1,000 of 1,000 (configuration 724ffb3a6a2d); full run 6,700 of 6,700 (configuration 08616c590e58) | data/reports/2019_pilot.json, data/reports/2019_full_run.json |
| Consistency across the five runs | reliability | intraclass correlation of the five runs' scores, ICC(1), for each score question | reported; no threshold before Study A | full run, 134 summaries: ICC(1) from 0.85 to 0.92 across the five score questions, 0.97 for the weighted score (pilot: 0.78 to 0.91) | data/reports/2019_pilot.json; the score agreement component's output for this judge (Study A, A1) |
<!-- END GENERATED FROM CONTRACT -->
