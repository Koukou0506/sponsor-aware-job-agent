from typing import Any


def build_job_review_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        score = float(item.get("total_score", 0.0))
        if score >= 72:
            recommendation = "apply"
        elif score >= 60:
            recommendation = "review"
        else:
            recommendation = "archive"
        selected_track = str(item.get("selected_resume_track", item.get("role_track", "")))
        rows.append(
            {
                **item,
                "recommendation": recommendation,
                "resume": (
                    "technical-v1"
                    if selected_track == "technical"
                    else "technical-business-v1"
                ),
                "evidence_count": len(item.get("evidence", [])),
                "requires_verification": bool(item.get("unresolved_items", [])),
            }
        )
    return rows


def render(service: object) -> None:
    import streamlit as st

    st.header("Job Review")
    rows = build_job_review_rows(service.list_job_reviews())
    if not rows:
        st.info("No pending jobs require review.")
        return

    labels = {
        f"{row['company']} — {row['title']} ({row['country']})": row
        for row in rows
    }
    selected_label = st.selectbox("Job", list(labels))
    row = labels[selected_label]

    left, right = st.columns(2)
    with left:
        st.metric("Total score", f"{row['total_score']:.1f}")
        st.write("Recommended resume:", row["resume"])
        st.write("Role track:", row["role_track"])
        st.write("Recommendation:", row["recommendation"])
        st.write("Strongest matches:", row.get("matching_evidence", []))
        st.write("Main gaps:", row.get("missing_requirements", []))
    with right:
        st.write("Work-authorisation status:", row["work_authorization_status"])
        st.write("Route:", row["route_type"])
        st.write("Evidence:", row.get("evidence", []))
        st.write("Unresolved:", row.get("unresolved_items", []))

    controls = st.columns(4)
    if controls[0].button("Generate package", disabled=row["materials_generated"]):
        service.generate_package(row["job_id"])
        st.success("Application package created for review.")
    if controls[1].button("Save"):
        service.set_job_review_status(row["review_id"], "saved")
        st.success("Job saved.")
    if controls[2].button("Reject"):
        service.set_job_review_status(row["review_id"], "rejected")
        st.success("Job removed from the review queue.")
    if controls[3].button("Needs verification"):
        service.set_job_review_status(row["review_id"], "needs_verification")
        st.warning("Job marked for verification.")
