# Resume-Ready Project Description

## Recommended two-bullet version

**Sponsor-Aware Job Agent | Python, SQLAlchemy, Playwright, Streamlit**

- Built a local-first job discovery and semi-automated application system integrating Greenhouse, Lever, Ashby and SmartRecruiters, with region-specific work-authorisation rules for the UK, Netherlands, Germany, Ireland and Hong Kong and separate ranking models for technical vs. technical-business roles.
- Designed a fact-constrained resume pipeline and human-in-the-loop Playwright workflow that traces generated claims to approved resume facts, pre-fills supported ATS fields, persists application state in SQLite, and intentionally blocks automated final submission and unresolved high-risk fields.

## Short one-bullet version

- Developed a Python-based sponsor-aware job application agent that combines ATS ingestion, five-region work-authorisation rules, dual-track job ranking, fact-grounded resume tailoring, SQLite persistence and supervised Playwright autofill across Greenhouse, Lever, Ashby and SmartRecruiters.

## Interview framing

The strongest technical discussion points are:

1. why work-authorisation eligibility is evaluated before skill matching;
2. how employer-sponsored, job-supported and candidate-owned routes are modeled differently;
3. how resume facts constrain generative rewriting;
4. why the system fails closed on uncertain browser fields and never submits automatically;
5. why a modular monolith was chosen over microservices for a local single-user MVP.
