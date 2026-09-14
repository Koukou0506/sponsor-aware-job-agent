from datetime import UTC, datetime
from typing import Any, Protocol

from job_agent.domain.ids import new_id
from job_agent.materials.models import Application, ApplicationEvent

_ALLOWED = {
    "discovered": {"filtered_out", "shortlisted"},
    "shortlisted": {"materials_generated", "withdrawn"},
    "materials_generated": {"awaiting_review"},
    "awaiting_review": {"approved", "rejected"},
    "approved": {"autofill_started", "withdrawn"},
    "autofill_started": {"ready_to_submit", "approved"},
    "ready_to_submit": {"submitted", "approved"},
    "submitted": {"screening", "interview", "rejected", "withdrawn"},
    "screening": {"interview", "rejected", "withdrawn"},
    "interview": {"offer", "rejected", "withdrawn"},
    "offer": set(),
    "rejected": set(),
    "withdrawn": set(),
    "filtered_out": set(),
}


class InvalidApplicationTransition(ValueError):
    pass


def allowed_transitions(current: str) -> tuple[str, ...]:
    if current not in _ALLOWED:
        raise InvalidApplicationTransition(f"unknown application state: {current}")
    return tuple(sorted(_ALLOWED[current]))


def can_transition(current: str, target: str) -> bool:
    return target in allowed_transitions(current)


class TrackerRepositories(Protocol):
    def get_application(self, application_id: str) -> Application | None: ...
    def save_application_event(
        self,
        application: Application,
        event: ApplicationEvent,
    ) -> None: ...
    def commit(self) -> None: ...


class ApplicationTracker:
    def __init__(self, repositories: TrackerRepositories) -> None:
        self._repositories = repositories

    def transition(
        self,
        application_id: str,
        new_state: str,
        payload: dict[str, Any] | None = None,
    ) -> ApplicationEvent:
        application = self._repositories.get_application(application_id)
        if application is None:
            raise KeyError(application_id)
        if not can_transition(application.current_state, new_state):
            raise InvalidApplicationTransition(
                f"cannot transition {application.current_state} to {new_state}"
            )
        now = datetime.now(UTC)
        updated = application.model_copy(
            update={
                "current_state": new_state,
                "submitted_at": now if new_state == "submitted" else application.submitted_at,
            }
        )
        event = ApplicationEvent(
            event_id=new_id("event"),
            application_id=application_id,
            from_state=application.current_state,
            to_state=new_state,
            payload=payload or {},
            created_at=now,
        )
        self._repositories.save_application_event(updated, event)
        self._repositories.commit()
        return event
