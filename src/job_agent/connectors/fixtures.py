import json
from pathlib import Path

from job_agent.connectors.ashby import AshbyConnector
from job_agent.connectors.base import BoardRef, RawJob
from job_agent.connectors.greenhouse import GreenhouseConnector
from job_agent.connectors.lever import LeverConnector
from job_agent.connectors.smartrecruiters import SmartRecruitersConnector


class FixtureConnector:
    """Offline connector used for deterministic tests and local demonstrations."""

    def __init__(self, platform: str, fixture_dir: Path) -> None:
        self._platform = platform
        self._fixture_path = fixture_dir / platform / "jobs.json"

    async def list_jobs(self, board: BoardRef) -> list[RawJob]:
        payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        if self._platform == "greenhouse":
            return GreenhouseConnector.map_payload(board.board_token, board.company_name, payload)
        if self._platform == "lever":
            return LeverConnector.map_payload(board.board_token, board.company_name, payload)
        if self._platform == "ashby":
            return AshbyConnector.map_payload(board.board_token, board.company_name, payload)
        if self._platform == "smartrecruiters":
            return [SmartRecruitersConnector.map_detail(board.board_token, board.company_name, item) for item in payload.get("content", [])]
        raise ValueError(f"unsupported fixture platform: {self._platform}")

    async def fetch_job(self, board: BoardRef, external_job_id: str) -> RawJob:
        return next(job for job in await self.list_jobs(board) if job.external_job_id == external_job_id)

    async def health_check(self, board: BoardRef) -> bool:
        await self.list_jobs(board)
        return True
