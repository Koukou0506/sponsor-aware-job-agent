from typing import Any

from job_agent.connectors._mapping import parse_datetime
from job_agent.connectors.base import BoardRef, RawJob
from job_agent.connectors.http import ResilientHttpClient


class AshbyConnector:
    def __init__(self, http: ResilientHttpClient | None = None) -> None:
        self._http = http or ResilientHttpClient()

    async def list_jobs(self, board: BoardRef) -> list[RawJob]:
        payload = await self._http.get_json(
            f"https://api.ashbyhq.com/posting-api/job-board/{board.board_token}"
        )
        return self.map_payload(board.board_token, board.company_name, payload)

    async def fetch_job(self, board: BoardRef, external_job_id: str) -> RawJob:
        jobs = await self.list_jobs(board)
        return next(job for job in jobs if job.external_job_id == external_job_id)

    async def health_check(self, board: BoardRef) -> bool:
        await self.list_jobs(board)
        return True

    @staticmethod
    def map_payload(
        board_token: str,
        company_name: str,
        payload: dict[str, Any],
    ) -> list[RawJob]:
        return [
            RawJob(
                platform="ashby",
                board_token=board_token,
                external_job_id=str(item["id"]),
                company_name=company_name,
                title=str(item["title"]),
                location_text=str(item.get("location", "")),
                description_html=str(item.get("descriptionHtml") or item.get("descriptionPlain") or ""),
                application_url=str(item["applyUrl"]),
                published_at=parse_datetime(item.get("publishedAt")),
                metadata={"department": item.get("department"), "team": item.get("team")},
                source_payload=item,
            )
            for item in payload.get("jobs", [])
            if item.get("isListed", True)
        ]
