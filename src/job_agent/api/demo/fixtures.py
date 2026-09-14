from __future__ import annotations
from copy import deepcopy

JOBS = [
    {
        "job_id": "job_demo_gb_1", "review_id": "review_demo_gb_1", "company": "Northstar Systems",
        "title": "Technical Implementation Consultant", "country": "GB", "city": "London",
        "role_track": "technical_business", "total_score": 88, "language": "English", "ats": "greenhouse",
        "published_at": "2026-09-14T08:00:00Z",
        "requirements": ["Python", "SQL", "cross-functional delivery"],
        "work_authorisation": {"status":"eligible","fit":0.95,"route":"UK_SKILLED_WORKER","confidence":0.93,
            "evidence":[{"kind":"official_registry","strength":"A","text":"Synthetic licensed sponsor match"}],
            "unresolved":[],"ruleset_version":"demo-2026-09"},
        "fit": {"total":88,"skill":82,"experience":78,"role_transition":94,"language":96,
            "strengths":["Python/SQL evidence","cross-functional coordination"],"gaps":["Limited consulting tenure"]},
        "review_status":"pending",
    },
    {
        "job_id": "job_demo_nl_1", "review_id": "review_demo_nl_1", "company": "Canal Analytics",
        "title": "Junior Data Engineer", "country": "NL", "city": "Amsterdam", "role_track": "technical",
        "total_score": 84, "language": "English", "ats": "lever", "published_at": "2026-09-13T09:00:00Z",
        "requirements":["Python","SQL","Docker"],
        "work_authorisation":{"status":"likely","fit":0.82,"route":"NL_HIGHLY_SKILLED_MIGRANT","confidence":0.82,
          "evidence":[{"kind":"official_registry","strength":"A","text":"Synthetic recognised sponsor match"}],
          "unresolved":["Salary not disclosed"],"ruleset_version":"demo-2026-09"},
        "fit":{"total":84,"skill":83,"experience":70,"role_transition":87,"language":95,"strengths":["Python modelling"],"gaps":["Production data pipelines"]},
        "review_status":"pending",
    },
    {
        "job_id":"job_demo_de_1","review_id":"review_demo_de_1","company":"Rhine Robotics","title":"Technical Project Coordinator",
        "country":"DE","city":"Berlin","role_track":"technical_business","total_score":81,"language":"English","ats":"ashby",
        "published_at":"2026-09-12T11:00:00Z","requirements":["project coordination","technical literacy"],
        "work_authorisation":{"status":"likely","fit":0.8,"route":"DE_SKILLED_WORKER","confidence":0.8,
          "evidence":[{"kind":"role_route","strength":"B","text":"Synthetic skilled-worker route fit"}],"unresolved":["Degree-role alignment review"],"ruleset_version":"demo-2026-09"},
        "fit":{"total":81,"skill":75,"experience":76,"role_transition":92,"language":94,"strengths":["TPM workflow"],"gaps":["German language not listed"]},
        "review_status":"saved",
    },
    {
        "job_id":"job_demo_ie_1","review_id":"review_demo_ie_1","company":"Liffey Cloud","title":"Cloud Support Engineer",
        "country":"IE","city":"Dublin","role_track":"technical","total_score":77,"language":"English","ats":"smartrecruiters",
        "published_at":"2026-09-11T10:00:00Z","requirements":["Linux","Python","customer support"],
        "work_authorisation":{"status":"uncertain","fit":0.62,"route":"IE_CRITICAL_SKILLS","confidence":0.64,
          "evidence":[{"kind":"occupation","strength":"B","text":"Synthetic critical-skills category"}],"unresolved":["Exact occupation code","Salary"],"ruleset_version":"demo-2026-09"},
        "fit":{"total":77,"skill":78,"experience":65,"role_transition":80,"language":96,"strengths":["Linux/Python"],"gaps":["Cloud certification"]},
        "review_status":"needs_verification",
    },
    {
        "job_id":"job_demo_hk_1","review_id":"review_demo_hk_1","company":"Harbour AI","title":"Solutions Engineer",
        "country":"HK","city":"Hong Kong","role_track":"technical_business","total_score":86,"language":"English","ats":"greenhouse",
        "published_at":"2026-09-14T07:30:00Z","requirements":["Python","client delivery","English"],
        "work_authorisation":{"status":"eligible","fit":1.0,"route":"HK_TTPS_C","confidence":0.91,
          "evidence":[{"kind":"candidate_owned_route","strength":"A","text":"Synthetic TTPS candidate-owned route"}],"unresolved":[],"ruleset_version":"demo-2026-09"},
        "fit":{"total":86,"skill":81,"experience":75,"role_transition":95,"language":97,"strengths":["English","technical communication"],"gaps":["Pre-sales experience"]},
        "review_status":"pending",
    },
    {
        "job_id":"job_demo_gb_2","review_id":"review_demo_gb_2","company":"Maple Works","title":"Junior Product Operations Analyst",
        "country":"GB","city":"Manchester","role_track":"technical_business","total_score":65,"language":"English","ats":"lever",
        "published_at":"2026-09-10T09:00:00Z","requirements":["operations","analytics"],
        "work_authorisation":{"status":"ineligible","fit":0.0,"route":"UK_SKILLED_WORKER","confidence":0.99,
          "evidence":[{"kind":"jd_text","strength":"A","text":"Synthetic JD explicitly says no sponsorship"}],"unresolved":[],"ruleset_version":"demo-2026-09"},
        "fit":{"total":65,"skill":76,"experience":70,"role_transition":82,"language":96,"strengths":["analytics"],"gaps":["Work authorisation"]},
        "review_status":"rejected",
    },
    {
        "job_id":"job_demo_nl_2","review_id":"review_demo_nl_2","company":"Delta QA","title":"QA Automation Engineer",
        "country":"NL","city":"Rotterdam","role_track":"technical","total_score":73,"language":"English","ats":"ashby",
        "published_at":"2026-09-09T09:00:00Z","requirements":["Python","test automation"],
        "work_authorisation":{"status":"likely","fit":0.78,"route":"NL_HIGHLY_SKILLED_MIGRANT","confidence":0.76,
          "evidence":[{"kind":"official_registry","strength":"A","text":"Synthetic recognised sponsor match"}],"unresolved":["Salary threshold"],"ruleset_version":"demo-2026-09"},
        "fit":{"total":73,"skill":70,"experience":58,"role_transition":74,"language":95,"strengths":["Python"],"gaps":["Automation framework"]},
        "review_status":"saved",
    },
    {
        "job_id":"job_demo_de_2","review_id":"review_demo_de_2","company":"Spree Data","title":"Analytics Engineer",
        "country":"DE","city":"Berlin","role_track":"technical","total_score":79,"language":"English","ats":"smartrecruiters",
        "published_at":"2026-09-08T09:00:00Z","requirements":["SQL","Python","analytics engineering"],
        "work_authorisation":{"status":"uncertain","fit":0.55,"route":"DE_EU_BLUE_CARD","confidence":0.6,
          "evidence":[{"kind":"role_route","strength":"B","text":"Synthetic Blue Card route candidate"}],"unresolved":["Salary","Degree-role alignment"],"ruleset_version":"demo-2026-09"},
        "fit":{"total":79,"skill":80,"experience":61,"role_transition":82,"language":95,"strengths":["SQL/Python"],"gaps":["dbt"]},
        "review_status":"needs_verification",
    },
]

FACTS = [
 {"fact_id":"fact_demo_python","text":"Built Python models and data-processing workflows for astrophysics research.","source":"Synthetic demo resume","approved":True},
 {"fact_id":"fact_demo_coord","text":"Coordinated cross-functional project work and structured reporting workflows.","source":"Synthetic demo resume","approved":True},
 {"fact_id":"fact_demo_sql","text":"Used SQL for joins, aggregation and analytical queries.","source":"Synthetic demo resume","approved":True},
]

def seeded_state():
    return {"jobs": deepcopy(JOBS), "facts": deepcopy(FACTS), "packages": {}, "applications": {}}
