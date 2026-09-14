from typing import Any


def build_claim_rows(claims: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    for claim in claims:
        status = str(claim.get("validation_status", "unsupported"))
        has_sources = bool(claim.get("source_fact_ids")) and bool(
            claim.get("original_sources")
        )
        valid = status == "verified" and has_sources
        rows.append(
            {
                **claim,
                "severity": "success" if valid else "error",
            }
        )
    return rows, bool(rows) and all(row["severity"] == "success" for row in rows)


def render(service: object) -> None:
    import streamlit as st

    st.header("Application Package")
    package_ids = service.list_pending_package_ids()
    if not package_ids:
        st.info("No application packages are awaiting review.")
        return
    package_id = st.selectbox("Package", package_ids)
    package = service.get_package_review_view(package_id)
    rows, can_approve = build_claim_rows(package["claims"])

    st.write("Job:", package["job_title"])
    st.write("Company:", package["company"])
    st.write("Base resume:", package["base_resume_id"])
    st.write("Validation:", package["validation_status"])

    for row in rows:
        icon = "✅" if row["severity"] == "success" else "⛔"
        with st.expander(f"{icon} {row['text']}"):
            st.write("Fact IDs:", row["source_fact_ids"])
            st.write("Original sources:", row["original_sources"])
            st.write("Transformation:", row.get("transformation_type"))

    if package.get("screening_answers"):
        st.subheader("Screening answers")
        st.dataframe(package["screening_answers"], use_container_width=True, hide_index=True)
    if package.get("cover_letter_text"):
        st.subheader("Cover letter")
        st.text_area(
            "Draft",
            value=package["cover_letter_text"],
            height=240,
            disabled=True,
        )

    actions = st.columns(2)
    if actions[0].button("Approve package", disabled=not can_approve):
        service.approve_package(package_id)
        st.success("Package approved.")
    if actions[1].button("Reject package"):
        service.reject_package(package_id)
        st.warning("Package rejected.")
