from collections.abc import Callable
from typing import Any

from job_agent.bootstrap import ServiceFactory, build_service_factory
from job_agent.ui.pages import (
    application_package,
    application_tracker,
    autofill_queue,
    dashboard,
    job_review,
    resume_import,
    settings,
)

PageRenderer = Callable[[object], None]
ServiceBuilder = Callable[[ServiceFactory], Any]

PAGES: dict[str, tuple[PageRenderer, ServiceBuilder]] = {
    "Dashboard": (dashboard.render, lambda factory: factory.review_workspace_service()),
    "Job Review": (job_review.render, lambda factory: factory.review_workspace_service()),
    "Application Package": (
        application_package.render,
        lambda factory: factory.review_workspace_service(),
    ),
    "Autofill Queue": (
        autofill_queue.render,
        lambda factory: factory.autofill_workspace_service(),
    ),
    "Application Tracker": (
        application_tracker.render,
        lambda factory: factory.review_workspace_service(),
    ),
    "Settings": (
        settings.render,
        lambda factory: factory.operations_service(),
    ),
    "Resume Import": (
        resume_import.render,
        lambda factory: factory.resume_import_service(),
    ),
}


def main() -> None:
    import streamlit as st

    service_factory = build_service_factory()
    st.set_page_config(page_title="Sponsor-Aware Job Agent", layout="wide")
    page = st.sidebar.radio("Page", list(PAGES))
    renderer, service_builder = PAGES[page]
    renderer(service_builder(service_factory))


if __name__ == "__main__":
    main()
