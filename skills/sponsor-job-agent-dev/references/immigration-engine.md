# Immigration engine

Supported regions: GB, NL, DE, IE, HK.

Rules belong under `src/job_agent/immigration/` and must return:
- status / work-authorisation fit;
- route type;
- evidence;
- unresolved items;
- confidence where available;
- ruleset version.

Do not reduce the model to `sponsor=true/false`:
- UK/NL depend strongly on employer eligibility.
- Germany is route/job/degree/salary oriented rather than a sponsor-list model.
- Ireland distinguishes permit routes.
- Hong Kong TTPS is candidate-owned when approved; likely eligibility is not current work authorisation.
