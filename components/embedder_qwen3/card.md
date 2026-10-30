# Card: Qwen3-Embedding-8B embedder

**Purpose.** Turns summaries and feedback into vectors for Study A's comparisons of feedback (A4) and for the content measures, novelty and topics. One of three embedders from different families, so that a finding can be checked across them (design, Section 3).

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). The model is Qwen3-Embedding-8B, under the Apache-2.0 licence; sentence-transformers and transformers are under the Apache-2.0 licence.

**Data terms.** Each run sends the texts to a GPU container rented from Modal, under the project's paid account (design, Section 7). The container exists only while the run lasts, has no public endpoint and writes no text to its logs.

**How it embeds.**
- One text at a time, on an L40S GPU, with deterministic algorithms, so a text's vector does not depend on what else is embedded with it.
- It is the embedder that takes a task instruction; the same instruction is given to every text, so all its vectors are of one type.
- Vectors are L2-normalized; texts longer than 8,192 tokens are cut (none in 2019).

**Known failure modes.**
- Length moves embeddings; compare texts of similar length, or use measures robust to it.
- Not yet validated against human similarity ratings; that validation is future work (design, Section 3).

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `embedder_qwen3`, version 1.0.0, role representer, deterministic.
- **Configuration hash:** `880c10b871ae21d525173932e2cb0489a2271e07c7a36aaae5b926dca6f7846c`
- **Validation status:** provisional; population: Executive summaries and feedback of the competition's round 1, 2019
- **Model:** `{"engine": "sentence-transformers 6.1.0, transformers 5.19.0, torch 2.14.1, deterministic algorithms, one text at a time", "gpu": "L40S", "id": "Qwen/Qwen3-Embedding-8B", "licence": "Apache-2.0", "provider": "Modal", "revision": "1d8ad4ca9b3dd8059ad90a75d4983776a23d44af"}`
- **Tools:** modal 1.6.1
- **Settings:** `{"dtype": "bfloat16", "instruction": "Instruct: Represent the strengths and weaknesses of a business venture that this text describes or evaluates\nQuery:", "max_seq_length": 8192, "texts_per_call": 500}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Re-execution gives identical vectors | determinism | share of texts whose vectors are bit-identical when embedded again in a new container | 1.0 | pass: the 161 summaries embedded again in a new container gave bit-identical vectors | data/reports/2019_embedding_reexecution.json; the rerun is recorded beside the stored output |
| Agreement with the other embedders on pairwise distances | agreement | Spearman correlation of pairwise cosine similarities with each other embedder's | reported (design, Section 3); validation against human similarity ratings is future work | reported: with bge-m3 0.66 on feedback and 0.47 on summaries; with gte-modernbert 0.63 and 0.54 | the embedding agreement component's output; data/reports/2019_study_a_report.md, Section 4 |
<!-- END GENERATED FROM CONTRACT -->
