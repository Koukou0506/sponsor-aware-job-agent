def render(service: object) -> None:
    import streamlit as st

    st.header("Settings")
    st.json(service.settings_summary())
