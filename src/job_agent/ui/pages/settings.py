def render(service: object) -> None:
    import streamlit as st

    st.header("Operations & Settings")
    snapshot = service.settings_summary()
    columns = st.columns(4)
    columns[0].metric("Run success", f"{snapshot['run_success_rate']:.2f}%")
    columns[1].metric(
        "Low-confidence work authorisation",
        f"{snapshot['low_confidence_work_authorization_rate']:.2f}%",
    )
    columns[2].metric("Autofill completion", f"{snapshot['autofill_completion_rate']:.2f}%")
    columns[3].metric("Estimated LLM cost", f"${snapshot['estimated_cost']:.2f}")
    st.subheader("Connector health")
    st.dataframe(snapshot["connector_health"], use_container_width=True, hide_index=True)
    st.subheader("Hard-fail distribution")
    st.json(snapshot["hard_fail_distribution"])
