# Card: records tables

**Purpose.** Arranges a year's round 1 records into the four analysis tables of the design's Section 1.3 (entries, documents, evaluations, judges), linked by codes, so that no analysis needs the export with names in it.

**Owner.** The project's authors.

**Licence.** The code, contract and prompts under the MIT licence; this card under CC BY 4.0 (README, Licence). Uses openpyxl (MIT).

**Data terms.** Runs on project machines; sends nothing to any service. Its output contains free text that names ventures and people (the summaries, the judges' feedback, the form's written answers), so it stays in `data/`.

**What it drops and what it codes.** Names, email addresses, websites (only whether one was given is kept) and the form's attestation and referral answers are dropped. Entries and judges are identified by codes from the private key (`data/private/code_key.csv`), assigned by `pipeline/pseudonyms.py`.

**What it checks.** Each column it reads must sit where the contract says, with a header containing the expected fragments; a changed layout stops the run rather than filling the wrong column. The fragments avoid the competition's name, which the headers contain.

**Known failure modes.**
- The column positions are those of the 2019 export; another year's export with a different layout needs new settings, and so a new configuration hash.
- An entry judged but missing from the applications sheet gets a row with only what the judging sheet shows (one in 2019).
- The round 3 advancement column of the 2019 export is "No" for every team, so `finalist` and `winner` stay unknown: the records of rounds 2 and 3 cannot be obtained (design, Section 1.2).

**Version history.**
- 1.0.0: first version.

**Errata.** None.

## From the contract

<!-- BEGIN GENERATED FROM CONTRACT -->
- **Component:** `records_tables`, version 1.0.0, role extractor, deterministic.
- **Configuration hash:** `e7e6114bb11eeee797ed289f0b0d70db071d1b06fc0420a5e822fd4e0a92aeaf`
- **Validation status:** validated; population: The round 1 records of the competition, 2019 format
- **Tools:** openpyxl 3.1.5
- **Settings:** `{"applications": {"columns": {"advanced_r2": {"column": 8, "header": ["Advanced to", "Round 2"]}, "company_type": {"column": 14, "header": ["best fits your company"]}, "description": {"column": 12, "header": ["Describe your business"]}, "entity_formed": {"column": 18, "header": ["currently have an entity formed"]}, "entity_type": {"column": 19, "header": ["what type of entity"]}, "entry_identifier": {"column": 1, "header": ["Identifier"]}, "fields": {"column": 15, "header": ["fields/tags"]}, "milestones": {"column": 16, "header": ["milestones have you reached"]}, "milestones_other": {"column": 17, "header": ["If other(s)"]}, "pitch": {"column": 11, "header": ["high-level pitch"]}, "product_type": {"column": 13, "header": ["type of product"]}, "submitted": {"column": 3, "header": ["Submitted?"]}, "website": {"column": 20, "header": ["have a website"]}}, "sheet": "Worksheet"}, "judging": {"columns": {"Q1": {"column": 5, "header": ["overall quality of the business concept"]}, "Q10": {"column": 15, "header": ["strengths and weaknesses"]}, "Q2": {"column": 6, "header": ["quality of the company concept", "Score"]}, "Q2c": {"column": 7, "header": ["quality of the company concept", "Applicant Feedback"]}, "Q3": {"column": 8, "header": ["Comment on the viability and scalability"]}, "Q4": {"column": 9, "header": ["rate the viability and scalability", "Score"]}, "Q5": {"column": 10, "header": ["market attractiveness and exit potential", "Applicant Feedback"]}, "Q6": {"column": 11, "header": ["rate the market attractiveness", "Score"]}, "Q7": {"column": 12, "header": ["quality of the written work", "Score"]}, "Q8": {"column": 13, "header": ["improve their written submission"]}, "Q9": {"column": 14, "header": ["early stage investor", "Score"]}, "entry_identifier": {"column": 2, "header": ["Entry identifier"]}, "judge_email": {"column": 3, "header": ["Judge Email"]}, "rank": {"column": 0, "header": ["Rank"]}, "weighted": {"column": 16, "header": ["Weighted average"]}}, "sheet": "Worksheet 1"}}`
- **Persisted:** under the hashes of its inputs and configuration; never regenerated silently

| Check | Kind | Metric | Threshold | Result | Evidence |
|---|---|---|---|---|---|
| Unit tests on a synthetic workbook | unit_tests |  | all pass | pass | tests/test_records_tables.py |
| Structure of the 2019 tables | consistency | three evaluations per judged entry; five scores and five to six texts per evaluation; one rank per entry | no exceptions | pass: 135 entries with 3 evaluations each, none missing a score or a required text | data/reports/2019_profile.json (pipeline/stages/profile.py) |
| No listed sensitive term in the code and category columns | consistency | cells with a listed term or an email address | none | pass | data/reports/2019_sensitive_check.json (pipeline/stages/tables.py) |
<!-- END GENERATED FROM CONTRACT -->
