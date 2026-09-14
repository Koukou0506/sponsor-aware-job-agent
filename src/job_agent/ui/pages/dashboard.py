from typing import Any


def build_dashboard_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "today_discovered": int(summary.get("today_discovered", 0)),
        "pending_reviews": int(summary.get("pending_reviews", 0)),
        "pending_packages": int(summary.get("pending_packages", 0)),
        "application_funnel": {
            "submitted": int(summary.get("submitted", 0)),
            "interviews": int(summary.get("interviews", 0)),
            "offers": int(summary.get("offers", 0)),
        },
        "regional_distribution": dict(summary.get("regional_distribution", {})),
        "track_distribution": dict(summary.get("track_distribution", {})),
        "connector_health": list(summary.get("connector_health", [])),
        "estimated_cost": float(summary.get("estimated_cost", 0.0)),
        "run_success_rate": float(summary.get("run_success_rate", 0.0)),
        "low_confidence_work_authorization_rate": float(
            summary.get("low_confidence_work_authorization_rate", 0.0)
        ),
        "autofill_completion_rate": float(
            summary.get("autofill_completion_rate", 0.0)
        ),
    }


def render(service: object) -> None:
    import streamlit as st

    st.header("Dashboard")
    metrics = build_dashboard_metrics(service.dashboard_summary())
    columns = st.columns(4)
    columns[0].metric("Jobs discovered today", metrics["today_discovered"])
    columns[1].metric("Pending job reviews", metrics["pending_reviews"])
    columns[2].metric("Pending packages", metrics["pending_packages"])
    columns[3].metric("LLM cost", f"${metrics['estimated_cost']:.2f}")

    operations = st.columns(3)
    operations[0].metric("Run success", f"{metrics['run_success_rate']:.2f}%")
    operations[1].metric(
        "Low-confidence work authorisation",
        f"{metrics['low_confidence_work_authorization_rate']:.2f}%",
    )
    operations[2].metric(
        "Autofill completion",
        f"{metrics['autofill_completion_rate']:.2f}%",
    )

    st.subheader("Application funnel")
    st.dataframe(
        [
            {"stage": stage, "count": count}
            for stage, count in metrics["application_funnel"].items()
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Regional distribution")
    st.json(metrics["regional_distribution"])
    st.subheader("Role-track distribution")
    st.json(metrics["track_distribution"])
    st.subheader("Connector health")
    st.dataframe(metrics["connector_health"], use_container_width=True, hide_index=True)
