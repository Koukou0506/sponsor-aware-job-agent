from typing import Any


def build_mapping_rows(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "page_label": mapping["page_label"],
            "canonical_field": mapping["canonical_field"],
            "value": mapping["value"],
            "source": mapping["source"],
            "confidence": mapping["confidence"],
            "risk_level": mapping["risk_level"],
            "requires_review": mapping["requires_review"],
        }
        for mapping in mappings
    ]


def render(service: object) -> None:
    import streamlit as st

    st.header("Autofill Queue")
    st.caption(
        "The agent fills supported fields only. The external application's final "
        "submission remains a manual browser action."
    )
    queue = service.list_queue()
    if not queue:
        st.info("No approved applications are waiting for autofill review.")
        return

    labels = {
        f"{item['company']} — {item['job_title']} ({item['country']})": item
        for item in queue
    }
    item = labels[st.selectbox("Application", list(labels))]
    st.write("Application state:", item["current_state"])
    st.write("ATS:", item["ats_platform"])
    st.write("Application URL:", item["application_url"])

    if item["session_id"] is None:
        if st.button("Open browser and autofill"):
            pid = service.launch_browser(item["application_id"])
            st.success(f"Local browser worker started (PID {pid}). Refresh to review mappings.")
        return

    session = service.get_session_view(item["session_id"])
    st.subheader("Mapped fields")
    st.dataframe(
        build_mapping_rows(session["mappings"]),
        use_container_width=True,
        hide_index=True,
    )
    if session["stop_reasons"]:
        st.subheader("Stop reasons")
        st.dataframe(session["stop_reasons"], use_container_width=True, hide_index=True)
    st.write("Session state:", session["state"])

    if session["state"] in {"fields_mapped", "autofilled", "needs_review"}:
        reviewed = st.checkbox(
            "I reviewed every mapped field, including work-authorisation and salary fields.",
            key=f"reviewed_{session['session_id']}",
        )
        stops_resolved = True
        if session["stop_reasons"]:
            stops_resolved = st.checkbox(
                "I manually resolved every stop reason shown above in the external browser.",
                key=f"stops_{session['session_id']}",
            )
        confirmation = reviewed and stops_resolved
        if st.button("Confirm fields ready", disabled=not confirmation):
            service.confirm_ready(session["session_id"], confirmation=confirmation)
            st.success("Fields marked ready. Submit only in the external browser.")
    elif session["state"] == "ready_to_submit":
        submitted = st.checkbox(
            "I personally clicked submit in the external application and saw confirmation.",
            key=f"submitted_{session['session_id']}",
        )
        if st.button("Record manual submission", disabled=not submitted):
            service.mark_submitted_manually(
                session["session_id"],
                confirmation=submitted,
            )
            st.success("Manual submission recorded.")
