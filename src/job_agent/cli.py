from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

import typer
import yaml

from job_agent.config.loader import ConfigBundle
from job_agent.settings import Settings

if TYPE_CHECKING:
    from job_agent.connectors.base import BoardRef, JobConnector

app = typer.Typer(no_args_is_help=True)
db_app = typer.Typer(no_args_is_help=True)
resume_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(resume_app, name="resume")


def _phase_unavailable(phase: int) -> None:
    typer.echo(f"This command becomes available in Phase {phase}.")
    raise typer.Exit(code=2)


@app.command()
def doctor() -> None:
    settings = Settings.from_env()
    settings.ensure_directories()
    example_config_ok = True
    try:
        ConfigBundle.load(Path("config/examples"))
    except (OSError, ValueError):
        example_config_ok = False
    checks = {
        "configuration directory": settings.config_dir.is_dir(),
        "artifact directory": settings.artifact_dir.is_dir(),
        "browser profile directory": settings.browser_profile_dir.is_dir(),
        "database directory": _database_parent(settings.database_url).is_dir(),
        "example configuration": example_config_ok,
    }
    for label, ok in checks.items():
        typer.echo(f"{label}: {'ok' if ok else 'failed'}")
    if not all(checks.values()):
        raise typer.Exit(code=1)


def _database_parent(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        return Path(".")
    return Path(database_url.removeprefix("sqlite:///")).parent


@db_app.command("upgrade")
def db_upgrade() -> None:
    from alembic import command
    from alembic.config import Config

    settings = Settings.from_env()
    settings.ensure_directories()
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")
    typer.echo("database upgraded")


@resume_app.command("import")
def resume_import(
    path: Path,
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    from job_agent.resume_ingestion.extraction import HeuristicResumeExtractor
    from job_agent.resume_ingestion.service import ResumeImportService
    from job_agent.storage.database import build_engine, build_session_factory
    from job_agent.storage.resume_repositories import SqlAlchemyResumeRepositories

    settings = Settings.from_env()
    settings.ensure_directories()
    repositories = SqlAlchemyResumeRepositories(
        build_session_factory(build_engine(settings.database_url))
    )
    service = ResumeImportService(
        repositories=repositories,
        extractor=HeuristicResumeExtractor(),
        source_root=settings.artifact_dir / "resume_sources",
    )
    session = service.import_file(path, dry_run=dry_run)
    typer.echo(f"{session.import_id} {session.status}")


@resume_app.command("delete")
def resume_delete(
    source_id: str,
    mode: str = typer.Option("retain-facts", "--mode"),
) -> None:
    from job_agent.resume_ingestion.extraction import HeuristicResumeExtractor
    from job_agent.resume_ingestion.service import ResumeImportService
    from job_agent.storage.database import build_engine, build_session_factory
    from job_agent.storage.resume_repositories import SqlAlchemyResumeRepositories

    if mode not in {"retain-facts", "revoke-facts"}:
        raise typer.BadParameter("mode must be retain-facts or revoke-facts")
    settings = Settings.from_env()
    repositories = SqlAlchemyResumeRepositories(
        build_session_factory(build_engine(settings.database_url))
    )
    service = ResumeImportService(repositories, HeuristicResumeExtractor())
    source = service.delete_source(source_id, mode=mode)  # type: ignore[arg-type]
    typer.echo(f"{source.source_id} revoked")


def _load_boards(path: Path) -> list[BoardRef]:
    from job_agent.connectors.base import BoardRef

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [BoardRef.model_validate(item) for item in payload.get("boards", [])]


def _fixture_connectors(fixture_dir: Path) -> dict[str, JobConnector]:
    from job_agent.connectors.fixtures import FixtureConnector

    return {
        platform: FixtureConnector(platform, fixture_dir)
        for platform in ("greenhouse", "lever", "ashby", "smartrecruiters")
    }


def _live_connectors() -> dict[str, JobConnector]:
    from job_agent.connectors.ashby import AshbyConnector
    from job_agent.connectors.greenhouse import GreenhouseConnector
    from job_agent.connectors.lever import LeverConnector
    from job_agent.connectors.smartrecruiters import SmartRecruitersConnector

    return {
        "greenhouse": GreenhouseConnector(),
        "lever": LeverConnector(),
        "ashby": AshbyConnector(),
        "smartrecruiters": SmartRecruitersConnector(),
    }


def _load_registry_records(
    settings: Settings,
    *,
    fixture_mode: bool,
) -> list[RegistryRecord]:
    from job_agent.immigration.models import RegistryRecord
    from job_agent.immigration.registry import load_registry

    if fixture_mode:
        return [
            RegistryRecord(
                registry_record_id="uk-example",
                country="UK",
                legal_name="Example Limited",
                canonical_domain=None,
                registry_identifier="EX-UK",
                status="active",
                source="example",
                ruleset_version="example-v1",
            ),
            RegistryRecord(
                registry_record_id="nl-example",
                country="NL",
                legal_name="Example Ltd",
                canonical_domain=None,
                registry_identifier="EX-NL",
                status="active",
                source="example",
                ruleset_version="example-v1",
            ),
        ]

    registry_dir = settings.config_dir / "registries"
    records: list[RegistryRecord] = []
    if not registry_dir.exists():
        return records
    for path in sorted(registry_dir.iterdir()):
        if path.suffix.casefold() not in {".json", ".csv"}:
            continue
        imported, _checksum = load_registry(path)
        records.extend(imported)
    return records


def _upgrade_database(settings: Settings) -> None:
    from alembic import command
    from alembic.config import Config

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")


@app.command()
def ingest(
    fixture_dir: Path | None = typer.Option(None, "--fixture-dir"),
    board_config: Path = typer.Option(Path("config/examples/boards.yaml"), "--board-config"),
) -> None:
    boards = _load_boards(board_config)
    connectors = _fixture_connectors(fixture_dir) if fixture_dir else _live_connectors()

    async def fetch_count() -> int:
        total = 0
        for board in boards:
            total += len(await connectors[board.platform].list_jobs(board))
        return total

    typer.echo(f"fetched={asyncio.run(fetch_count())}")


@app.command()
def assess(candidate: str = typer.Option("default", "--candidate")) -> None:
    from sqlalchemy import func, select

    from job_agent.storage.database import build_engine, build_session_factory
    from job_agent.storage.orm import MatchAssessmentRow, WorkAuthorizationAssessmentRow

    settings = Settings.from_env()
    settings.ensure_directories()
    _upgrade_database(settings)
    with build_session_factory(build_engine(settings.database_url))() as session:
        work_auth = session.scalar(select(func.count()).select_from(WorkAuthorizationAssessmentRow).where(WorkAuthorizationAssessmentRow.candidate_id == candidate)) or 0
        matches = session.scalar(select(func.count()).select_from(MatchAssessmentRow).where(MatchAssessmentRow.candidate_id == candidate)) or 0
    typer.echo(f"candidate={candidate} work_authorization={work_auth} matches={matches}")


@app.command("run-daily")
def run_daily(
    fixture_dir: Path | None = typer.Option(None, "--fixture-dir"),
    board_config: Path = typer.Option(Path("config/examples/boards.yaml"), "--board-config"),
    candidate: str = typer.Option("default", "--candidate"),
) -> None:
    from job_agent.application.daily_pipeline import CandidateSnapshot, DailyPipeline
    from job_agent.storage.database import build_engine, build_session_factory
    from job_agent.storage.job_intelligence import SqlAlchemyJobIntelligenceStore

    settings = Settings.from_env()
    settings.ensure_directories()
    _upgrade_database(settings)
    boards = _load_boards(board_config)
    connectors = _fixture_connectors(fixture_dir) if fixture_dir else _live_connectors()
    records = _load_registry_records(settings, fixture_mode=fixture_dir is not None)
    store = SqlAlchemyJobIntelligenceStore(build_session_factory(build_engine(settings.database_url)))
    snapshot = CandidateSnapshot(candidate_id=candidate, skills={"python", "sql", "linux", "project management", "implementation"}, languages={"english", "mandarin"}, experience_years=1.0, route_status={"HK": "likely_eligible"})
    try:
        summary = asyncio.run(DailyPipeline(connectors=connectors, store=store, registry_records=records).run(boards, snapshot))
    finally:
        store.close()
    typer.echo(f"discovered={summary.discovered_count} duplicates={summary.duplicate_count} hard_failed={summary.hard_failed_count} review_queue={summary.review_queue_count}")


@app.command()
def generate(
    job_id: str = typer.Option(..., "--job-id"),
    candidate: str = typer.Option("default", "--candidate"),
    cover_letter: bool = typer.Option(False, "--cover-letter"),
) -> None:
    from job_agent.application.packages import PackageService
    from job_agent.materials.screening import load_fixed_answer_resolver
    from job_agent.storage.application_repositories import (
        SqlAlchemyApplicationRepositories,
    )
    from job_agent.storage.database import build_engine, build_session_factory

    settings = Settings.from_env()
    settings.ensure_directories()
    _upgrade_database(settings)
    repositories = SqlAlchemyApplicationRepositories(
        build_session_factory(build_engine(settings.database_url))
    )
    try:
        package = PackageService(
            repositories,
            load_fixed_answer_resolver(settings.config_dir / "screening_answers.yaml"),
        ).generate(
            job_id,
            candidate,
            cover_letter=cover_letter,
        )
    finally:
        repositories.close()
    typer.echo(
        f"package={package.package_id} "
        f"validation={package.validation_status} "
        f"review={package.review_status}"
    )


def _load_autofill_profile_answers(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    aliases = {
        "linkedin": "linkedin_url",
        "github": "github_url",
    }
    supported = {
        "full_name",
        "first_name",
        "last_name",
        "email",
        "phone",
        "location",
        "linkedin_url",
        "github_url",
    }
    answers: dict[str, object] = {}
    for key, value in payload.items():
        canonical = aliases.get(str(key), str(key))
        if canonical in supported and isinstance(value, str | bool | list):
            answers[canonical] = {"value": value, "source": "profile.yaml"}
    return answers


@app.command()
def autofill(
    application_id: str = typer.Option(..., "--application-id"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    fixture_page: Path | None = typer.Option(None, "--fixture-page"),
    browser_executable: str | None = typer.Option(None, "--browser-executable"),
    keep_open: bool = typer.Option(False, "--keep-open"),
) -> None:
    from job_agent.autofill.field_mapping import FieldMapper
    from job_agent.autofill.service import AutofillService, PlaywrightBrowserFactory
    from job_agent.autofill.workspace import default_adapters
    from job_agent.storage.autofill_repositories import SqlAlchemyAutofillRepositories
    from job_agent.storage.database import build_engine, build_session_factory

    settings = Settings.from_env()
    settings.ensure_directories()
    _upgrade_database(settings)
    repositories = SqlAlchemyAutofillRepositories(
        build_session_factory(build_engine(settings.database_url)),
        artifact_dir=settings.artifact_dir,
    )
    context = repositories.get_application_context(application_id)
    if context is None:
        repositories.close()
        raise typer.BadParameter(f"unknown application: {application_id}")
    executable = browser_executable or os.environ.get(
        "JOB_AGENT_BROWSER_EXECUTABLE"
    )
    if executable is None and Path("/usr/bin/chromium").exists():
        executable = "/usr/bin/chromium"
    browser_factory = PlaywrightBrowserFactory(
        settings.browser_profile_dir,
        headless=dry_run,
        executable_path=executable,
    )
    service = AutofillService(
        repositories,
        default_adapters(),
        FieldMapper(),
        browser_factory=browser_factory,
        base_answer_catalog=_load_autofill_profile_answers(
            settings.config_dir / "profile.yaml"
        ),
    )

    async def run() -> None:
        page = (
            await browser_factory.open_html(fixture_page)
            if fixture_page is not None
            else await browser_factory.open(str(context.application_url))
        )
        try:
            session = await service.prepare(
                application_id,
                page=page,
                dry_run=dry_run,
            )
            typer.echo(f"session={session.session_id} state={session.state}")
            for mapping in session.field_mappings:
                typer.echo(
                    f"field={mapping.canonical_field} source={mapping.source} "
                    f"confidence={mapping.confidence:.2f} review={mapping.requires_review}"
                )
            for reason in session.stop_reasons:
                typer.echo(f"stop={reason.code}: {reason.detail}")
            if keep_open and not dry_run:
                typer.echo(
                    "Browser remains open for manual review and manual submission. "
                    "Close the browser window when finished."
                )
                await page.wait_for_event("close")
        finally:
            await browser_factory.close()

    try:
        asyncio.run(run())
    finally:
        repositories.close()


@app.command("evaluate-golden")
def evaluate_golden(path: Path) -> None:
    from job_agent.evaluation.golden import (
        evaluate_golden_cases,
        load_golden_cases,
        report_rows,
    )

    report = evaluate_golden_cases(load_golden_cases(path))
    typer.echo(f"cases={report.case_count} passed={report.passed}")
    for row in report_rows(report):
        typer.echo(
            f"{row['metric']}: value={row['value']} "
            f"target={row['target']} passed={row['passed']}"
        )
    if not report.passed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
