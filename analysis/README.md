# Analyses

The analyses of Study A, the illustration, and Study B, the reproducibility audit (`docs/design.md`, Sections 4 and 5). The validators and aggregators in `components/` compute them, and the stages `pipeline/stages/study_a.py` and `pipeline/stages/study_b.py` run them. They read the tables in `data/tables/` and the components' stored outputs, and report aggregates only.
