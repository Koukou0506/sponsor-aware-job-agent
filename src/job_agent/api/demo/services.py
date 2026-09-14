from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from .fixtures import seeded_state

class DemoServices:
    def __init__(self) -> None:
        self._state = seeded_state()

    def dashboard(self) -> dict[str, Any]:
        jobs=self._state["jobs"]
        eligible=sum(j["work_authorisation"]["status"] in {"eligible","likely"} for j in jobs)
        high=sum(j["total_score"]>=80 and j["work_authorisation"]["fit"]>=0.5 for j in jobs)
        apps=list(self._state["applications"].values())
        return {
          "counts":{"new_jobs":len(jobs),"work_authorisation_eligible":eligible,"high_fit":high,
                    "awaiting_review":sum(j["review_status"] in {"pending","needs_verification"} for j in jobs),
                    "ready_to_submit":sum(a["current_state"]=="ready_to_submit" for a in apps),
                    "interviews":sum(a["current_state"] in {"interview","offer"} for a in apps)},
          "country_distribution":self._distribution(jobs,"country"),
          "track_distribution":self._distribution(jobs,"role_track"),
          "application_funnel":self._distribution(apps,"current_state"),
          "recent_high_fit_jobs":[self._job_summary(j) for j in sorted(jobs,key=lambda x:x["total_score"],reverse=True)[:5]],
          "alerts":[{"severity":"info","message":"Demo Mode uses synthetic data only."}],
        }

    @staticmethod
    def _distribution(items:list[dict[str,Any]], key:str)->list[dict[str,Any]]:
        counts:dict[str,int]={}
        for item in items:
            value=str(item.get(key,"unknown")); counts[value]=counts.get(value,0)+1
        return [{"key":k,"count":v} for k,v in sorted(counts.items())]

    @staticmethod
    def _job_summary(j:dict[str,Any])->dict[str,Any]:
        return {k:deepcopy(j[k]) for k in ["job_id","review_id","company","title","country","city","role_track","total_score","language","ats","published_at","review_status"]} | {"work_authorisation":deepcopy(j["work_authorisation"])}

    def list_jobs(self, filters:dict[str,Any]) -> dict[str,Any]:
        items=[self._job_summary(j) for j in self._state["jobs"]]
        mapping={"country":"country","role_track":"role_track","work_authorisation":"wa","company":"company","language":"language","ats":"ats"}
        for q,field in mapping.items():
            value=filters.get(q)
            if value in (None,""): continue
            if field=="wa": items=[j for j in items if j["work_authorisation"]["status"]==value]
            elif field=="company": items=[j for j in items if str(value).casefold() in j["company"].casefold()]
            else: items=[j for j in items if str(j[field]).casefold()==str(value).casefold()]
        if filters.get("min_score") is not None: items=[j for j in items if j["total_score"]>=float(filters["min_score"])]
        page=max(1,int(filters.get("page") or 1)); size=min(100,max(1,int(filters.get("page_size") or 25))); total=len(items)
        start=(page-1)*size
        return {"items":items[start:start+size],"page":page,"page_size":size,"total":total}

    def get_job(self, job_id:str)->dict[str,Any]:
        for j in self._state["jobs"]:
            if j["job_id"]==job_id: return deepcopy(j)
        raise KeyError(job_id)

    def set_review_status(self, job_id:str,status:str)->dict[str,Any]:
        if status not in {"pending","saved","rejected","needs_verification"}: raise ValueError("unsupported review status")
        job=self.get_job(job_id)
        for row in self._state["jobs"]:
            if row["job_id"]==job_id: row["review_status"]=status; job=row; break
        return deepcopy(job)

    def create_package(self, job_id:str, cover_letter:bool=False, force:bool=False)->dict[str,Any]:
        job=self.get_job(job_id)
        pid=f"pkg_{job_id}"
        if force or pid not in self._state["packages"]:
            facts=self._state["facts"]
            claims=[
              {"claim_id":f"claim_{job_id}_1","text":"Applied Python and SQL to analyse complex datasets and communicate evidence-backed findings.",
               "source_fact_ids":["fact_demo_python","fact_demo_sql"],"source_facts":[facts[0],facts[2]],"transformation_type":"tailored","validation_status":"verified","reviewer_approved":False},
              {"claim_id":f"claim_{job_id}_2","text":"Coordinated structured project work across technical and non-technical stakeholders.",
               "source_fact_ids":["fact_demo_coord"],"source_facts":[facts[1]],"transformation_type":"tailored","validation_status":"verified","reviewer_approved":False},
            ]
            self._state["packages"][pid]={"package_id":pid,"job_id":job_id,"job_title":job["title"],"company":job["company"],
              "base_resume_id":"demo_technical" if job["role_track"]=="technical" else "demo_technical_business",
              "validation_status":"verified","review_status":"awaiting_review","claims":claims,
              "screening_answers":[
                {"question":"Will you require employer sponsorship?","answer":"This demo uses a synthetic work-authorisation profile.","source_type":"fixed_fact","requires_review":True,"risk_level":"high"},
                {"question":"Why this role?","answer":f"The role aligns with the synthetic candidate's {job['role_track']} transition profile.","source_type":"generated_draft","requires_review":True,"risk_level":"medium"},
              ],
              "cover_letter_text": (f"Dear Hiring Team,\n\nThis synthetic demo application is tailored for {job['title']} at {job['company']}.\n\nSincerely,\nDemo Candidate" if cover_letter else None),
            }
        return deepcopy(self._state["packages"][pid])

    def get_package(self,pid:str)->dict[str,Any]:
        if pid not in self._state["packages"]: raise KeyError(pid)
        return deepcopy(self._state["packages"][pid])

    def approve_package(self,pid:str)->dict[str,Any]:
        pkg=self.get_package(pid)
        if any(c["validation_status"]!="verified" for c in pkg["claims"]): raise ValueError("package contains unsupported claims")
        self._state["packages"][pid]["review_status"]="approved"
        app_id=f"app_{pkg['job_id']}"
        self._state["applications"].setdefault(app_id,{"application_id":app_id,"package_id":pid,"job_id":pkg["job_id"],
          "job_title":pkg["job_title"],"company":pkg["company"],"country":self.get_job(pkg["job_id"])["country"],
          "current_state":"approved","autofill_status":"not_started","submitted_at":None,"outcome":None})
        return self.get_package(pid)

    def reject_package(self,pid:str)->dict[str,Any]:
        if pid not in self._state["packages"]: raise KeyError(pid)
        self._state["packages"][pid]["review_status"]="rejected"
        return self.get_package(pid)

    def list_applications(self)->list[dict[str,Any]]:
        return [deepcopy(v) for v in self._state["applications"].values()]

    def transition_application(self,app_id:str,new_state:str,payload:dict[str,Any]|None=None)->dict[str,Any]:
        allowed={"approved":{"autofill_started","withdrawn"},"autofill_started":{"ready_to_submit","approved"},
                 "ready_to_submit":{"submitted","approved"},"submitted":{"screening","interview","rejected","withdrawn"},
                 "screening":{"interview","rejected","withdrawn"},"interview":{"offer","rejected","withdrawn"},
                 "offer":set(),"rejected":set(),"withdrawn":set()}
        app=self._state["applications"].get(app_id)
        if app is None: raise KeyError(app_id)
        if new_state not in allowed.get(app["current_state"],set()): raise ValueError(f"cannot transition {app['current_state']} to {new_state}")
        app["current_state"]=new_state
        if new_state=="submitted": app["submitted_at"]=datetime.now(timezone.utc).isoformat()
        return deepcopy(app)

    def list_resume_facts(self)->dict[str,Any]:
        return {"approved_facts":deepcopy(self._state["facts"]),"pending_imports":[]}
    def import_resume(self, filename:str, content:bytes)->dict[str,Any]: raise PermissionError("resume upload disabled in demo")
    def get_resume_import(self, import_id:str)->dict[str,Any]: raise KeyError(import_id)
    def approve_resume_fact(self, fact_id:str, import_id:str)->dict[str,Any]: raise PermissionError("resume mutation disabled in demo")
    def reject_resume_fact(self, fact_id:str, import_id:str)->dict[str,Any]: raise PermissionError("resume mutation disabled in demo")
    def reassess_immigration(self, job_id:str)->dict[str,Any]: raise PermissionError("real reassessment disabled in demo")

    def immigration_overview(self)->dict[str,Any]:
        return {"routes":[{"country":j["country"],"status":j["work_authorisation"]["status"],"route":j["work_authorisation"]["route"],
                           "confidence":j["work_authorisation"]["confidence"],"ruleset_version":j["work_authorisation"]["ruleset_version"],
                           "evidence":j["work_authorisation"]["evidence"],"unresolved":j["work_authorisation"]["unresolved"]}
                          for j in self._state["jobs"][:5]],
                "registry_status":[{"country":c,"status":"synthetic","freshness":"demo"} for c in ["GB","NL","DE","IE","HK"]]}

    def settings_summary(self)->dict[str,Any]:
        return {"mode":"demo","database":{"configured":False},"candidate_profile":{"configured":True,"synthetic":True},
                "registries":{"configured":True,"synthetic":True},"browser_profile":{"configured":False},"llm":{"configured":False}}

    def reset(self)->None: self._state=seeded_state()

class DemoServiceFactory:
    @staticmethod
    def create()->DemoServices:
        return DemoServices()
