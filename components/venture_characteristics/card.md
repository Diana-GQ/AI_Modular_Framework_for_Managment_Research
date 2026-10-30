# Card: venture characteristics

**Purpose.** Turns the application form's answers into indicators of the ventures' substance for A5: type of company and product, fields, milestones, legal entity and website.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses pandas (BSD).

**Data terms.** Runs on project machines; sends nothing to any service.

**Known failure modes.**
- Self-reported by the teams, and coarse.
- The free-text type of legal entity is reduced to a few categories by pattern; unusual wordings fall into 'other'.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `venture_characteristics`, version 1.0.0, role extractor, deterministic.
- **Configuration hash:** `51b390c6204af4c0283b48df4459b514302608393a40e472ecc37a6742ad037d`
- **Validation status:** validated; population: The applications of the competition, 2019 form
- **Tools:** pandas 3.0.6
- **Settings:** `{"internet_company_type": "Internet and Consumer Technology", "milestones": ["Core business concept defined", "Prototype/MVP built", "Company registered/incorporated", "First external users on the product", "Funding raised", "First client has paid"], "min_entries_per_field": 10, "product_types": ["Software/App", "Physical Product", "Data/Analytics", "Service", "Electronic Hardware", "Local Business", "Education/Training", "Consulting", "Perishables", "Other"]}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on synthetic answers | unit_tests |  | all pass | pass | tests/test_phase5.py |
<!-- END GENERATED FROM CONTRACT -->
