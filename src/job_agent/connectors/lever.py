from typing import Any

from job_agent.connectors.base import BoardRef, RawJob
from job_agent.connectors.http import ResilientHttpClient


class LeverConnector:
    def __init__(self, http: ResilientHttpClient | None = None) -> None:
        self._http = http or ResilientHttpClient()

    async def list_jobs(self, board: BoardRef) -> list[RawJob]:
        base = str(board.base_url or "https://api.lever.co")
        payload = await self._http.get_json(
            f"{base.rstrip('/')}/v0/postings/{board.board_token}",
            params={"mode": "json"},
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
        payload: list[dict[str, Any]],
    ) -> list[RawJob]:
        return [
            RawJob(
                platform="lever",
                board_token=board_token,
                external_job_id=str(item["id"]),
                company_name=company_name,
                title=str(item["text"]),
                location_text=str((item.get("categories") or {}).get("location", "")),
                description_html=str(item.get("descriptionPlain") or item.get("description") or ""),
                application_url=str(item.get("applyUrl") or item["hostedUrl"]),
                metadata={
                    "categories": item.get("categories", {}),
                    "workplaceType": item.get("workplaceType"),
                },
                source_payload=item,
            )
            for item in payload
        ]
