from typing import Any

from job_agent.resume_ingestion.models import ExtractedFactCandidate

_SEVERITY = {
    "new_fact": "info",
    "duplicate": "success",
    "wording_variant": "success",
    "metric_conflict": "error",
    "date_conflict": "error",
    "status_conflict": "error",
    "unsupported_claim": "error",
}


def build_review_rows(candidates: list[ExtractedFactCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_fact_id": candidate.candidate_fact_id,
            "fact": candidate.raw_fact,
            "classification": candidate.merge_classification,
            "matched_fact_id": candidate.matched_fact_id,
            "source_page": candidate.provenance.page_number,
            "confidence": candidate.provenance.extraction_confidence,
            "severity": _SEVERITY[candidate.merge_classification],
            "action_required": candidate.merge_classification
            in {"metric_conflict", "date_conflict", "status_conflict", "unsupported_claim"},
        }
        for candidate in candidates
    ]


def render(service: object) -> None:
    import streamlit as st

    st.header("Resume Import")
    uploaded = st.file_uploader("Upload resume", type=["pdf", "docx", "txt", "md"])
    if uploaded is None:
        return
    source_path = service.stage_uploaded_file(uploaded.name, uploaded.getvalue())
    if st.button("Parse resume"):
        st.session_state["resume_import"] = service.import_file(source_path)
    session = st.session_state.get("resume_import")
    if session is None:
        return
    rows = build_review_rows(session.extracted_facts)
    st.dataframe(rows, use_container_width=True, hide_index=True)
    for candidate in session.extracted_facts:
        with st.expander(candidate.raw_fact):
            st.caption(candidate.provenance.original_text)
            decision = st.selectbox(
                "Decision",
                [
                    "Accept",
                    "Edit",
                    "Reject",
                    "Merge with Existing",
                    "Mark as Wording Variant",
                    "Resolve Conflict",
                ],
                key=candidate.candidate_fact_id,
            )
            if st.button("Apply decision", key=f"apply_{candidate.candidate_fact_id}"):
                service.apply_review_decision(
                    session.import_id,
                    candidate.candidate_fact_id,
                    decision,
                )
