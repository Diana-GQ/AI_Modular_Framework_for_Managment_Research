# An AI Framework of Modular Components for Traceability and Reproducibility in Organizational Research

This repository holds a framework for building AI-assisted research pipelines from modular components with explicit, enforceable contracts. It also holds the pipeline of the framework's illustration, a comparison of human and AI evaluations of the entries to a university business plan competition, and a synthetic competition on which every step can be rerun. It accompanies the paper of the same title.

## Why

AI is increasingly used in organizational research. That raises a question of method: how can researchers make AI-assisted findings traceable and reproducible? Large language models (LLMs) may return different outputs to identical prompts, and providers update and retire their models. In a multi-step pipeline, that variability passes from one step to the next. The answer lies partly in how the pipelines that use those models are designed. Even when an AI output cannot be reproduced exactly, a pipeline can record how it was generated, keep the evidence behind each analytical decision, and let others examine the results.

## The framework

The framework adapts three ideas from software engineering: modular components, encapsulation and design by contract. A pipeline is divided into *components*, each with one defined task. A component consists of three files:
- its source code, `component.py`;
- its *contract*, `contract.yaml`, a machine-readable specification that the pipeline enforces every time the component runs;
- its *card*, `card.md`, documentation for human readers.

The contract has four sections:
- **Typed:** the kind, meaning and allowed values of every input and output.
- **Pinned:** everything that can change an output. That means the code, the prompts, the model and its exact version or weights, every setting, and the versions of the software packages.
- **Persisted:** how the outputs are stored. Each output is stored under a key made of two hashes, of its inputs and of the component's configuration, and is never regenerated silently.
- **Validated:** the checks the outputs must pass. For each check, it gives the threshold, the result obtained and the file that holds the evidence. It also gives the data on which the component was validated, and its status, provisional or validated.

The card states the component's purpose, owner, licence, data terms, known failure modes, version history and errata. Its last section is generated from the contract.

Because each output is stored under the hashes of its inputs and its configuration, any output can be traced to the data, code, model and settings behind it. A pipeline can be audited one component at a time, rerun, and each new output compared with the stored one. A component can be replaced by an equivalent, such as one that calls a different LLM, to test whether the findings still hold.

The pipeline also blocks errors of method ([`pipeline/checks.py`](pipeline/checks.py)). Vectors of different types cannot be compared. The outputs of a component whose status is not "validated", or of a stochastic component with no reliability estimate, cannot enter a regression or a test. That is why novelty, which has no human ratings to validate it, is described but not tested.

## The illustration

The framework is illustrated on round 1 of the 2019 edition of an annual business plan competition for university students:
- **Human evaluations.** 405 evaluations of 135 entries by 64 judges, three per entry. Each judge scored five criteria from 1 to 10 (concept, business model, market, written work and investor interest) and commented on each.
- **Executive summaries.** The two-page executive summaries of the judged entries; 134 are available.
- **AI evaluations.** The judges' ten questions, a score and a comment for each criterion, were posed to two AI judges, one question per call, five times each. They are Claude Sonnet 5.5 (Claude), a proprietary model reached through Anthropic's API, and Qwen3-8B (Qwen), an open-weight model served on a rented GPU.
- **Text analyses.** Three open-weight embedding models represent every summary and comment, and a profiler measures each summary's style and language.

Twenty-three components produce every number in the study. Four more generate the synthetic competition.

[`docs/design.md`](docs/design.md) describes the study: Study A, the illustration, and Study B, the reproducibility audit.

## The synthetic competition

The competition's records may not be shared. So this repository carries a synthetic competition of 40 invented ventures and 15 simulated judges, under the fictional year 2000, with the files and layout of a real edition ([`synthetic/README.md`](synthetic/README.md)). No real record entered it. Its scores were simulated from rounded aggregates of the 2019 records, and Claude Sonnet 5.5 wrote its summaries and comments. The whole pipeline runs on it, and its results can be reproduced.

### Reproducing its results

You need [uv](https://docs.astral.sh/uv/) and git. The repository holds the pipeline's outputs on the synthetic competition, in `synthetic/data/store/` and `synthetic/data/tables/`. They are the stored outputs of every component except the four that generated the competition, with their provenance records, and the analysis tables. Run:

```
uv run python -m pipeline.stages.study_b reproduce synthetic
```

The command:
- copies the repository into a new folder, without those outputs, and builds a new environment from `uv.lock`;
- brings in the stored outputs of the components that call a model, the two AI judges and the three embedders;
- computes every other output again: text extraction, the analysis tables, and all of Study A's analyses and its report;
- compares each new output with the one in the repository.

It calls no model and costs nothing. It takes about six minutes, and writes its findings to `synthetic/data/reports/2000_b1_reproduction.json`: the share of outputs reproduced exactly, the tables and reports that match, and the time taken.

To call the models yourself instead, you need an Anthropic API key, as `ANTHROPIC_API_KEY` in `.env`, and a [Modal](https://modal.com) account, set up with `uv run modal setup`. Move `synthetic/data/store/` and `synthetic/data/tables/` out of the repository first: the pipeline reuses every stored output, so with them in place the run only re-executes the embedders. Then run `uv run python -m pipeline.stages.synthetic run`. Claude's answers will be new draws. The open-weight judge (Qwen3-8B on an H100 GPU, served by vLLM in batch-invariant mode) and the three embedders should give identical outputs. The run costs about $16 at list prices.

## Running the pipeline

The stages run the components over a year's records, in this order. On the synthetic competition, set `COMPAI_DATA=$PWD/synthetic/data` and use the year 2000; its reproduction is `study_b reproduce synthetic`, as above. The stages that call Anthropic or Modal cost money.

```
uv run python -m pipeline.stages.pseudonymize <year>           # codes in place of identities
uv run python -m pipeline.stages.extract <year>                # the summaries' texts, and the extraction checks
uv run python -m pipeline.stages.tables <year>                 # the four analysis tables, and their sensitive-term check
uv run python -m pipeline.stages.profile <year>                # a profile of the records, in counts only
uv run modal run pipeline/modal_qwen.py::fetch                 # the open-weight judge's weights, into Modal's volume
uv run python -m pipeline.stages.judge pilot <year>            # both AI judges on the pilot's 20 summaries
uv run python -m pipeline.stages.judge report <year>           # the pilot's report
uv run python -m pipeline.stages.judge determinism <year>      # the open-weight judge's determinism test
uv run python -m pipeline.stages.judge full <year>             # both AI judges on every judged summary
uv run python -m pipeline.stages.judge full-report <year>      # what is stored or missing, and the AI answers' table
uv run modal run pipeline/modal_embed.py::fetch                # the embedders' weights, into Modal's volume
uv run python -m pipeline.stages.study_a embed <year>          # the three embedders, on Modal
uv run python -m pipeline.stages.study_a embed-check <year>    # the embedders re-executed in new containers
uv run python -m pipeline.stages.study_a report <year>         # every analysis of Study A, and its report
uv run python -m pipeline.stages.study_b reproduce <year>      # B1 (design, Section 5): the analysis rebuilt in a fresh copy
uv run python -m pipeline.freeze check                         # whether every component matches the frozen list
```

On the synthetic competition, `uv run python -m pipeline.stages.synthetic run` runs the stages from `pseudonymize` to the Study A report in turn, once the models' weights are in Modal's volume. In place of the full determinism test it runs a shorter precheck. [`docs/README.md`](docs/README.md) lists every stage, with the components it runs.

## A component, for example

[`components/claude_judge/`](components/claude_judge/) is the main AI judge. It asks Claude Sonnet 5.5 one of the ten questions about one executive summary.
- [`component.py`](components/claude_judge/component.py) is the code.
- [`contract.yaml`](components/claude_judge/contract.yaml) declares its inputs and outputs, pins the model, prompts, settings and package version, and records its checks. All 6,700 of its answers in the full run parsed, and its five runs agree with an intraclass correlation, ICC(1), of 0.98 on the weighted score.
- [`card.md`](components/claude_judge/card.md) documents its purpose, data terms, known failure modes and version history.

Its configuration hash is `1a53fe88c1da14e405f6b5e7c4e14274f05c324d143c4b9d7f2294cc8cdc4531`. Any change to its code, prompts, model or settings would give another hash, and new outputs beside the stored ones.

## Writing a component

A component is a folder in `components/` with three files:
- `component.py` defines `run(inputs, settings)`.
- `contract.yaml` declares the typed, pinned, persisted and validated sections.
- `card.md` is the documentation. Its last section is generated from the contract with `uv run python -m pipeline.cards components/<name>`.

The runner ([`pipeline/runner.py`](pipeline/runner.py)) does the rest:
- It checks inputs and outputs against the contract.
- It refuses a pinned package at another version.
- It computes the configuration hash, a fingerprint of everything that can change an output.
- It stores each output under its inputs and configuration, and writes the provenance record.

`components/frozen.json` records every component's version and configuration hash; a test fails if one changes. To change a frozen component, give it a new version, record the change on its card, and record the frozen list again with `uv run python -m pipeline.freeze record`.

## What is here

| Folder | Contents |
|---|---|
| [`docs/`](docs/README.md) | The study design, and a guide to the code's citations |
| [`pipeline/`](pipeline/) | The framework's code: contracts, the runner that enforces them, the store, provenance records, cards, the methodological checks and the model clients |
| [`pipeline/stages/`](pipeline/stages/) | The scripts that run the components over a year's records, step by step |
| [`components/`](components/) | One folder per component: `component.py`, `contract.yaml` and `card.md`; `shared/` holds what several components share, such as the AI judges' prompts |
| [`synthetic/`](synthetic/README.md) | The synthetic competition, the pipeline's outputs and reports on it, and how it was made |
| [`tests/`](tests/) | Tests, on synthetic data, with stand-ins for the model services |
| [`scripts/check_sensitive.py`](scripts/check_sensitive.py) | The check that keeps identifying terms out of git |
| [`data/`](data/README.md) | Empty here: the competition's records stay on the authors' machines |

## Tests

```
uv run pytest
```

## Data and confidentiality

The competition's records, and everything derived from them, are not in this repository and may not be shared. That includes the summaries, the comments, the AI outputs and the embeddings. The synthetic competition replaces them. Entries and judges are identified by random codes, and a check built from the records keeps names of people, ventures and institutions out of every commit. The records left the authors' computers only through two paid services, Anthropic's API and Modal, with data-sharing options off ([`docs/design.md`](docs/design.md), Section 7).

## Licence

The code is licensed under the MIT licence ([`LICENSE`](LICENSE)), and so are the contracts, the prompts and the other files the components read. The documentation is licensed under CC BY 4.0 ([`docs/LICENSE`](docs/LICENSE)). That covers the documents in `docs/`, the README files and the components' cards (`card.md`). The synthetic competition is also licensed under CC BY 4.0 ([`synthetic/LICENSE`](synthetic/LICENSE)). The licences do not cover the five score questions (Q2, Q4, Q6, Q7 and Q9 in [`docs/design.md`](docs/design.md), Section 2.1).
