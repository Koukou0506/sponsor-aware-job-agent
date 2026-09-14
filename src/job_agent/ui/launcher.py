import sys
from pathlib import Path

import typer


def main() -> None:
    try:
        from streamlit.web import cli as streamlit_cli
    except ImportError:
        typer.echo("Streamlit is not installed. Install the web extra with: pip install -e '.[web]'")
        raise SystemExit(2) from None
    app_path = Path(__file__).with_name("app.py")
    sys.argv = ["streamlit", "run", str(app_path)]
    raise SystemExit(streamlit_cli.main())
