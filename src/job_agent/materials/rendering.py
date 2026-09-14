from collections.abc import Callable
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from job_agent.materials.validation import ValidationReport

PdfBackend = Callable[[str, Path], Path]


class ResumeRenderer:
    def __init__(
        self,
        template_dir: Path,
        *,
        pdf_backend: PdfBackend | None = None,
    ) -> None:
        self._environment = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self._pdf_backend = pdf_backend or _playwright_pdf

    def render_html(
        self,
        context: dict[str, object],
        validation_report: ValidationReport,
    ) -> str:
        if not validation_report.export_allowed:
            raise ValueError("invalid application material cannot be rendered")
        return self._environment.get_template("resume.html.j2").render(**context)

    def render_pdf(
        self,
        context: dict[str, object],
        validation_report: ValidationReport,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = self.render_html(context, validation_report)
        return self._pdf_backend(html, output_path)


def render_cover_letter_pdf(text: str, output_path: Path) -> Path:
    paragraphs = "".join(
        f"<p>{escape(paragraph)}</p>"
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    )
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<style>@page{size:A4;margin:20mm}body{font-family:Arial,sans-serif;"
        "font-size:11pt;line-height:1.5;color:#111}p{white-space:pre-wrap}</style>"
        f"</head><body>{paragraphs}</body></html>"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return _playwright_pdf(html, output_path)


def _playwright_pdf(html: str, output_path: Path) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install the web optional dependency to render PDF") from exc
    with sync_playwright() as playwright:
        system_chromium = Path("/usr/bin/chromium")
        if system_chromium.exists():
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=str(system_chromium),
                args=["--no-sandbox"],
            )
        else:
            browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(path=str(output_path), format="A4", print_background=True)
        browser.close()
    return output_path
