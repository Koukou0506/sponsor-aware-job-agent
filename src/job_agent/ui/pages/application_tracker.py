from collections import defaultdict
from typing import Any


def group_applications_by_state(
    applications: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for application in applications:
        grouped[str(application["current_state"])].append(application)
    return dict(grouped)


def render(service: object) -> None:
    import streamlit as st

    st.header("Application Tracker")
    grouped = group_applications_by_state(service.list_applications())
    if not grouped:
        st.info("No applications have been created.")
        return
    for state, applications in grouped.items():
        st.subheader(state.replace("_", " ").title())
        for application in applications:
            with st.expander(
                f"{application['company']} — {application['job_title']}"
            ):
                st.write("Application ID:", application["application_id"])
                st.write("Submitted at:", application.get("submitted_at"))
                transitions = service.allowed_transitions(
                    application["current_state"]
                )
                if not transitions:
                    st.caption("Terminal state")
                    continue
                target = st.selectbox(
                    "Move to",
                    transitions,
                    key=f"target_{application['application_id']}",
                )
                note = st.text_input(
                    "Outcome note",
                    key=f"note_{application['application_id']}",
                )
                if st.button(
                    "Record transition",
                    key=f"transition_{application['application_id']}",
                ):
                    service.transition_application(
                        application["application_id"],
                        target,
                        {"note": note} if note else {},
                    )
                    st.success("Application state updated.")
