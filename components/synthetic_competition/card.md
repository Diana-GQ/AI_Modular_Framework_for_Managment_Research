# Card: synthetic competition

**Purpose.** Designs the synthetic competition that the public repository carries in place of the real records, which may not be shared (design, B4): 40 fictional ventures with their answers to the application form, 15 fictional judges with personas, three judges per venture drawn at random, and their scores on the five criteria. The top 30% of ventures by mean weighted score advance.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence).

**Data terms.** Runs locally; sends nothing to any service. Only rounded aggregates of the 2019 records enter its settings: the criteria's means and standard deviations, the shares of their variance between entries and between judges, and the shares of the form's answers. No record enters.

**How it simulates.**
- Each venture has a hidden quality and a hidden quality of writing, standard normal and correlated 0.5. The writers of the summaries see both, as words, never as numbers (`synthetic_summary`).
- A score is the criterion's mean plus three parts: the venture's part (its quality, or its quality of writing for the written work, plus something particular to the venture), the judge's part (a severity shared across criteria, plus something particular to the criterion), and the judge's reaction to the venture. Each part's share of the variance follows the settings. The reactions share an overall impression across the five criteria (the halo, 0.85).
- Scores are rounded and kept within 1 to 10, which shrinks the variance a little.

**Known failure modes.** The simulated judges differ from real ones in ways the settings do not capture: their scores depend on the venture's hidden quality, not on the summary they would have read. The synthetic competition shows the pipeline at work; it tests nothing about real judges.

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `synthetic_competition`, version 1.0.0, role generator, deterministic.
- **Configuration hash:** `3cc192cce50c98e12455315413fbe18e4a33a929d45dd7ae8d6f1fab99849b09`
- **Validation status:** provisional; population: The synthetic competition
- **Tools:** numpy 2.5.4
- **Settings:** `{"advance_share": 0.3, "company_types": ["Internet and Consumer Technology", "Non-Internet and Consumer Technology ( everything else)"], "criteria": {"business_model": {"entry": 0.2, "judge": 0.23, "mean": 5.9, "sd": 2.2}, "concept": {"entry": 0.28, "judge": 0.21, "mean": 6.4, "sd": 2.3}, "investor_interest": {"entry": 0.23, "judge": 0.19, "mean": 5.5, "sd": 2.8}, "market": {"entry": 0.16, "judge": 0.19, "mean": 6.1, "sd": 2.4}, "written_work": {"entry": 0.29, "judge": 0.21, "mean": 6.3, "sd": 2.3}}, "entity_types": ["LLC", "C Corp", "LLC", "LLC", "C Corp", "S Corp"], "entries": 40, "halo": 0.85, "judges": 15, "judges_per_entry": 3, "personas": ["a serial entrepreneur who writes terse, blunt comments and cares most about customers and traction", "a professor of entrepreneurship who writes careful, balanced comments about the logic of the business model", "an angel investor who writes short comments focused on market size, competition and returns", "a corporate innovation manager who writes encouraging comments with practical suggestions", "a startup lawyer who writes brief comments and notes legal, regulatory and structural gaps", "a product designer who writes informal comments about the product and the user experience", "a retired executive who writes polite, general comments and few specifics", "a venture capital associate who writes pointed comments on scalability and unit economics", "a mentor at a university incubator who writes friendly comments aimed at helping students improve", "an engineer turned founder who writes technical comments and doubts unproven claims", "a marketing consultant who writes comments about positioning, branding and the pitch", "a finance professional who writes comments about financial projections and assumptions", "a social entrepreneur who writes comments about impact and the needs of users", "an alumnus who runs a small business and writes plain, practical comments", "a healthcare investor who writes comments about evidence, regulation and adoption"], "probabilities": {"entity_formed": 0.6, "fields": {"Analytics": 0.2, "Cleantech": 0.1, "Consumer Goods": 0.15, "Education": 0.1, "Financial Services": 0.1, "Food and Beverage": 0.1, "Health": 0.2, "Mobile": 0.1, "Software": 0.2, "Technology": 0.3}, "internet_company": 0.5, "milestones": {"Company registered/incorporated": 0.55, "Core business concept defined": 0.95, "First client has paid": 0.2, "First external users on the product": 0.4, "Funding raised": 0.2, "Prototype/MVP built": 0.7}, "product_types": {"Consulting": 0.05, "Data/Analytics": 0.35, "Education/Training": 0.1, "Electronic Hardware": 0.2, "Local Business": 0.1, "Perishables": 0.05, "Physical Product": 0.45, "Service": 0.3, "Software/App": 0.6}, "website": 0.6}, "weights": {"business_model": 0.2, "concept": 0.2, "investor_interest": 0.3, "market": 0.2, "written_work": 0.1}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests | unit_tests |  | all pass | pass | tests/test_synthetic.py |
| The simulated judges resemble the 2019 judges | consistency | shares of variance between ventures, judges and residual, and halo, measured by the human benchmark and score agreement components on the synthetic records | reported beside the 2019 values | reported: shares between ventures of 0.28, 0.19, 0.05, 0.19 and 0.15 on concept, business model, market, written work and investor interest, against 0.28, 0.20, 0.16, 0.29 and 0.23 in the settings, rounded from 2019; shares from the judges' severity of 0.27 to 0.40, against 0.19 to 0.23; halo, the mean correlation of an evaluation's five scores, 0.70. With 40 ventures and 15 judges the shares are imprecise; the simulated judges differ more in severity than the settings intend | synthetic/data/reports/2000_study_a_report.md, Sections 1 and 2; the 2019 values are this contract's settings |
<!-- END GENERATED FROM CONTRACT -->
