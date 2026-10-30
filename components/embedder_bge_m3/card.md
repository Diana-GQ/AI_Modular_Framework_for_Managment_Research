# Card: bge-m3 embedder

**Purpose.** Turns summaries and feedback into vectors for Study A's comparisons of feedback (A4) and for the content measures, novelty and topics. One of three embedders from different families, so that a finding can be checked across them (design, Section 3).

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). The model is bge-m3, under the MIT licence; sentence-transformers and transformers are under the Apache-2.0 licence.

**Data terms.** Each run sends the texts to a GPU container rented from Modal, under the project's paid account (design, Section 7). The container exists only while the run lasts, has no public endpoint and writes no text to its logs.

**How it embeds.**
- One text at a time, on an L40S GPU, with deterministic algorithms, so a text's vector does not depend on what else is embedded with it.
- It takes no instruction; only its dense vectors are used.
- Vectors are L2-normalized; texts longer than 8,192 tokens are cut (none in 2019).

**Known failure modes.**
- Length moves embeddings; compare texts of similar length, or use measures robust to it.
- Not yet validated against human similarity ratings; that validation is future work (design, Section 3).

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `embedder_bge_m3`, version 1.0.0, role representer, deterministic.
- **Configuration hash:** `b5c4063356578ef5b8c1160529c99b0bf32f1f7417f36e4a2f8c244893ca4a30`
- **Validation status:** provisional; population: Executive summaries and feedback of the competition's round 1, 2019
- **Model:** `{"engine": "sentence-transformers 6.1.0, transformers 5.19.0, torch 2.14.1, deterministic algorithms, one text at a time", "gpu": "L40S", "id": "BAAI/bge-m3", "licence": "MIT", "provider": "Modal", "revision": "5617a9f61b028005a4858fdac845db406aefb181"}`
- **Tools:** modal 1.6.1
- **Settings:** `{"dtype": "float32", "instruction": null, "max_seq_length": 8192, "texts_per_call": 500}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Re-execution gives identical vectors | determinism | share of texts whose vectors are bit-identical when embedded again in a new container | 1.0 | pass: the 161 summaries embedded again in a new container gave bit-identical vectors | data/reports/2019_embedding_reexecution.json; the rerun is recorded beside the stored output |
| Agreement with the other embedders on pairwise distances | agreement | Spearman correlation of pairwise cosine similarities with each other embedder's | reported (design, Section 3); validation against human similarity ratings is future work | reported: with gte-modernbert 0.75 on feedback and 0.53 on summaries; with Qwen3-Embedding 0.66 and 0.47 | the embedding agreement component's output; data/reports/2019_study_a_report.md, Section 4 |
<!-- END GENERATED FROM CONTRACT -->
