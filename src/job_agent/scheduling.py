from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Sequence

from job_agent.application.daily_pipeline import CandidateSnapshot, DailyPipeline
from job_agent.cli import (
    _fixture_connectors,
    _live_connectors,
    _load_boards,
    _load_registry_records,
    _upgrade_database,
)
from job_agent.settings import Settings
from job_agent.storage.database import build_engine, build_session_factory
from job_agent.storage.job_intelligence import SqlAlchemyJobIntelligenceStore


def run_daily(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m job_agent.scheduling")
    parser.add_argument("command", nargs="?", default="run-daily")
    parser.add_argument("--fixture-dir", type=Path)
    parser.add_argument(
        "--board-config",
        type=Path,
        default=Path("config/examples/boards.yaml"),
    )
    parser.add_argument("--candidate", default="default")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command != "run-daily":
        parser.error("only run-daily is supported")

    settings = Settings.from_env()
    settings.ensure_directories()
    _upgrade_database(settings)
    boards = _load_boards(args.board_config)
    connectors = (
        _fixture_connectors(args.fixture_dir)
        if args.fixture_dir is not None
        else _live_connectors()
    )
    records = _load_registry_records(
        settings,
        fixture_mode=args.fixture_dir is not None,
    )
    store = SqlAlchemyJobIntelligenceStore(
        build_session_factory(build_engine(settings.database_url))
    )
    snapshot = CandidateSnapshot(
        candidate_id=args.candidate,
        skills={"python", "sql", "linux", "project management", "implementation"},
        languages={"english", "mandarin"},
        experience_years=1.0,
        route_status={"HK": "likely_eligible"},
    )
    try:
        summary = asyncio.run(
            DailyPipeline(
                connectors=connectors,
                store=store,
                registry_records=records,
            ).run(boards, snapshot)
        )
    finally:
        store.close()
    print(
        " ".join(
            [
                f"discovered={summary.discovered_count}",
                f"duplicates={summary.duplicate_count}",
                f"hard_failed={summary.hard_failed_count}",
                f"review_queue={summary.review_queue_count}",
            ]
        )
    )
    return 0 if summary.discovered_count >= summary.review_queue_count else 1


if __name__ == "__main__":
    raise SystemExit(run_daily())
