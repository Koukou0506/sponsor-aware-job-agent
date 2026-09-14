from collections.abc import Callable
from typing import Protocol
from datetime import UTC, datetime

from job_agent.domain.ids import new_id
from job_agent.domain.models import RunRecord


class RunSink(Protocol):
    def save(self, record: RunRecord) -> None: ...


class RunService:
    def __init__(
        self,
        sink: RunSink,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sink = sink
        self._clock = clock

    def start(self, run_type: str, workspace_id: str = "default") -> RunRecord:
        record = RunRecord(
            run_id=new_id("run"),
            workspace_id=workspace_id,
            run_type=run_type,
            started_at=self._clock(),
        )
        self._sink.save(record)
        return record

    def finish(
        self,
        record: RunRecord,
        *,
        processed: int,
        succeeded: int,
        skipped: int,
        failed: int,
    ) -> RunRecord:
        if min(processed, succeeded, skipped, failed) < 0:
            raise ValueError("run counts cannot be negative")
        if succeeded + skipped + failed > processed:
            raise ValueError("outcome counts cannot exceed processed count")
        finished = record.model_copy(
            update={
                "completed_at": self._clock(),
                "processed_count": processed,
                "success_count": succeeded,
                "skipped_count": skipped,
                "failed_count": failed,
            }
        )
        self._sink.save(finished)
        return finished
