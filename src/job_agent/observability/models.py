from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OperationsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ConnectorHealthMetric(OperationsModel):
    platform: str
    board_token: str
    status: str
    checked_at: datetime
    last_error: str | None = None


class OperationsSnapshot(OperationsModel):
    total_runs: int = 0
    processed_jobs: int = 0
    successful_jobs: int = 0
    skipped_jobs: int = 0
    failed_jobs: int = 0
    run_success_rate: float = Field(default=0.0, ge=0, le=100)
    low_confidence_work_authorization_rate: float = Field(default=0.0, ge=0, le=100)
    hard_fail_rate: float = Field(default=0.0, ge=0, le=100)
    duplicate_suppression_rate: float = Field(default=0.0, ge=0, le=100)
    validation_failure_rate: float = Field(default=0.0, ge=0, le=100)
    autofill_completion_rate: float = Field(default=0.0, ge=0, le=100)
    manual_submission_count: int = 0
    token_usage: int = 0
    estimated_cost: float = 0.0
    hard_fail_distribution: dict[str, int] = Field(default_factory=dict)
    connector_health: list[ConnectorHealthMetric] = Field(default_factory=list)
