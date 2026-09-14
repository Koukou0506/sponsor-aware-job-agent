from __future__ import annotations
from typing import Any
from fastapi import Request
from job_agent.api.demo.services import DemoServiceFactory
from job_agent.api.mode import Capabilities
from job_agent.bootstrap import build_service_factory

class LocalProductServices:
    def __init__(self) -> None:
        factory = build_service_factory()
        self.review = factory.review_workspace_service()
        self.autofill = factory.autofill_workspace_service()
        self.resume = factory.resume_import_service()

    def dashboard(self) -> dict[str, Any]:
        raw = self.review.dashboard_summary()
        return {
            "counts": {
                "new_jobs": raw.get("today_discovered", 0),
                "work_authorisation_eligible": raw.get("work_authorization_eligible", raw.get("eligible_jobs", 0)),
                "high_fit": raw.get("high_fit_jobs", 0),
                "awaiting_review": raw.get("pending_reviews", 0),
                "ready_to_submit": raw.get("ready_to_submit", 0),
                "interviews": raw.get("interviews", 0),
            },
            "country_distribution": [{"key": k, "count": v} for k, v in sorted(raw.get("regional_distribution", {}).items())],
            "track_distribution": [{"key": k, "count": v} for k, v in sorted(raw.get("track_distribution", {}).items())],
            "application_funnel": [],
            "recent_high_fit_jobs": self.list_jobs({"page_size": 5})["items"],
            "alerts": [],
        }

    @staticmethod
    def _summary(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": row["job_id"], "review_id": row.get("review_id"), "company": row["company"],
            "title": row["title"], "country": row["country"], "city": row.get("city"),
            "role_track": row["role_track"], "total_score": row["total_score"], "language": None,
            "ats": None, "published_at": None, "review_status": row.get("review_status", "pending"),
            "work_authorisation": {
                "status": row["work_authorization_status"], "fit": row["work_authorization_fit"],
                "route": row.get("route_type"), "confidence": None, "evidence": row.get("evidence", []),
                "unresolved": row.get("unresolved_items", []), "ruleset_version": None,
            },
        }

    def list_jobs(self, filters: dict[str, Any]) -> dict[str, Any]:
        rows = [self._summary(r) for r in self.review.list_job_reviews()]
        for key in ("country", "role_track"):
            value = filters.get(key)
            if value: rows = [r for r in rows if str(r[key]).casefold() == str(value).casefold()]
        wa = filters.get("work_authorisation")
        if wa: rows = [r for r in rows if r["work_authorisation"]["status"] == wa]
        company = filters.get("company")
        if company: rows = [r for r in rows if str(company).casefold() in r["company"].casefold()]
        if filters.get("min_score") is not None: rows = [r for r in rows if r["total_score"] >= float(filters["min_score"])]
        page=max(1,int(filters.get("page") or 1)); size=min(100,max(1,int(filters.get("page_size") or 25))); total=len(rows)
        start=(page-1)*size
        return {"items": rows[start:start+size], "page": page, "page_size": size, "total": total}

    def get_job(self, job_id: str) -> dict[str, Any]:
        for row in self.review.list_job_reviews():
            if row["job_id"] == job_id:
                summary = self._summary(row)
                summary.update({
                    "requirements": [],
                    "fit": {"total": row["total_score"], "skill": None, "experience": None, "role_transition": None, "language": None,
                            "strengths": row.get("matching_evidence", []), "gaps": row.get("missing_requirements", [])},
                })
                return summary
        raise KeyError(job_id)

    def set_review_status(self, job_id: str, status: str) -> dict[str, Any]:
        for row in self.review.list_job_reviews():
            if row["job_id"] == job_id:
                self.review.set_job_review_status(row["review_id"], status)
                result=self.get_job(job_id); result["review_status"] = status; return result
        raise KeyError(job_id)

    def create_package(self, job_id: str, cover_letter: bool = False, force: bool = False) -> dict[str, Any]:
        pid = self.review.generate_package(job_id, cover_letter=cover_letter, force=force)
        return self.review.get_package_review_view(pid)
    def get_package(self, package_id: str) -> dict[str, Any]: return self.review.get_package_review_view(package_id)
    def approve_package(self, package_id: str) -> dict[str, Any]: self.review.approve_package(package_id); return self.review.get_package_review_view(package_id)
    def reject_package(self, package_id: str) -> dict[str, Any]: self.review.reject_package(package_id); return self.review.get_package_review_view(package_id)
    def list_applications(self) -> list[dict[str, Any]]: return self.review.list_applications()
    def transition_application(self, application_id: str, new_state: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.review.transition_application(application_id, new_state, payload)
        for app in self.review.list_applications():
            if app["application_id"] == application_id: return app
        raise KeyError(application_id)
    def launch_autofill(self, application_id: str) -> dict[str, Any]:
        pid = self.autofill.launch_browser(application_id)
        return {"application_id": application_id, "process_id": pid, "status": "launched"}
    def get_autofill(self, session_id: str) -> dict[str, Any]: return self.autofill.get_session_view(session_id)
    def confirm_ready(self, session_id: str, confirmation: bool) -> dict[str, Any]: return self.autofill.confirm_ready(session_id, confirmation=confirmation)
    def mark_submitted_manually(self, session_id: str, confirmation: bool) -> dict[str, Any]: return self.autofill.mark_submitted_manually(session_id, confirmation=confirmation)
    def list_resume_facts(self) -> dict[str, Any]:
        approved = [fact.model_dump(mode="json") for fact in self.resume._repositories.facts.list_approved("default")]  # noqa: SLF001
        return {"approved_facts": approved, "pending_imports": []}
    def import_resume(self, filename: str, content: bytes) -> dict[str, Any]:
        staged = self.resume.stage_uploaded_file(filename, content)
        try:
            return self.resume.import_file(staged).model_dump(mode="json")
        finally:
            staged.unlink(missing_ok=True)
    def get_resume_import(self, import_id: str) -> dict[str, Any]:
        session = self.resume._repositories.imports.get(import_id)  # noqa: SLF001
        if session is None: raise KeyError(import_id)
        return session.model_dump(mode="json")
    def approve_resume_fact(self, fact_id: str, import_id: str) -> dict[str, Any]:
        return self.resume.approve_candidate(import_id, fact_id).model_dump(mode="json")
    def reject_resume_fact(self, fact_id: str, import_id: str) -> dict[str, Any]:
        return self.resume.reject_candidate(import_id, fact_id).model_dump(mode="json")
    def immigration_overview(self) -> dict[str, Any]:
        jobs = self.review.list_job_reviews()
        return {"routes": [{"job_id": j["job_id"], "country": j["country"], "status": j["work_authorization_status"], "route": j.get("route_type"),
                            "confidence": None, "ruleset_version": None, "evidence": j.get("evidence", []), "unresolved": j.get("unresolved_items", [])}
                           for j in jobs], "registry_status": []}
    def reassess_immigration(self, job_id: str) -> dict[str, Any]:
        # Current persisted assessment is returned without pretending that a registry refresh occurred.
        # Full recomputation belongs to the existing daily pipeline after registry refresh.
        job = self.get_job(job_id)
        return {"job_id": job_id, "assessment": job["work_authorisation"], "reassessed": False,
                "message": "Run the configured daily pipeline after refreshing registries for a full reassessment."}
    def settings_summary(self) -> dict[str, Any]:
        raw=self.review.settings_summary()
        return {"mode":"local","database":{"configured":bool(raw.get("database"))},"candidate_profile":{"configured":True},
                "registries":{"configured":True},"browser_profile":{"configured":True},"llm":{"configured":False}}

def get_product_services(request: Request):
    if hasattr(request.app.state, "product_services"):
        return request.app.state.product_services
    request.app.state.product_services = LocalProductServices()
    return request.app.state.product_services

def get_capabilities(request: Request) -> Capabilities:
    return request.app.state.capabilities
