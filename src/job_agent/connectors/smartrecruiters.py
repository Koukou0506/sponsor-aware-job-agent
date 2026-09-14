from typing import Any

from job_agent.connectors._mapping import parse_datetime
from job_agent.connectors.base import BoardRef, RawJob
from job_agent.connectors.http import ResilientHttpClient


class SmartRecruitersConnector:
    def __init__(self, http: ResilientHttpClient | None = None) -> None:
        self._http = http or ResilientHttpClient()

    async def list_jobs(self, board: BoardRef) -> list[RawJob]:
        base_url = (
            f"https://api.smartrecruiters.com/v1/companies/"
            f"{board.board_token}/postings"
        )
        limit = 100
        offset = 0
        summaries: list[dict[str, Any]] = []
        while True:
            payload = await self._http.get_json(
                base_url,
                params={"limit": limit, "offset": offset},
            )
            page = payload.get("content", [])
            summaries.extend(page)
            total = int(payload.get("totalFound", len(summaries)))
            if not page or len(summaries) >= total:
                break
            offset += limit

        result: list[RawJob] = []
        for item in summaries:
            detail = await self._http.get_json(f"{base_url}/{item['id']}")
            result.append(
                self.map_detail(board.board_token, board.company_name, detail)
            )
        return result

    async def fetch_job(self, board: BoardRef, external_job_id: str) -> RawJob:
        detail = await self._http.get_json(
            f"https://api.smartrecruiters.com/v1/companies/{board.board_token}/postings/{external_job_id}"
        )
        return self.map_detail(board.board_token, board.company_name, detail)

    async def health_check(self, board: BoardRef) -> bool:
        await self._http.get_json(
            f"https://api.smartrecruiters.com/v1/companies/{board.board_token}/postings",
            params={"limit": 1, "offset": 0},
        )
        return True

    @staticmethod
    def map_detail(board_token: str, company_name: str, item: dict[str, Any]) -> RawJob:
        location = item.get("location") or {}
        location_text = ", ".join(
            str(part) for part in (location.get("city"), location.get("country")) if part
        )
        sections = ((item.get("jobAd") or {}).get("sections") or {})
        description_parts: list[str] = []
        for section in sections.values():
            if isinstance(section, dict) and section.get("text"):
                description_parts.append(str(section["text"]))
        return RawJob(
            platform="smartrecruiters",
            board_token=board_token,
            external_job_id=str(item["id"]),
            company_name=company_name,
            title=str(item.get("name") or item.get("title") or ""),
            location_text=location_text,
            description_html="\n".join(description_parts),
            application_url=str(
                item.get("applyUrl")
                or item.get("ref")
                or f"https://jobs.smartrecruiters.com/{board_token}/{item['id']}"
            ),
            published_at=parse_datetime(item.get("releasedDate")),
            metadata={"location": location, "typeOfEmployment": item.get("typeOfEmployment")},
            source_payload=item,
        )
