def test_streamlit_launcher_module_exists():
    import importlib.util
    assert importlib.util.find_spec('job_agent.ui.launcher') is not None
