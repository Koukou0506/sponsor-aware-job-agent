from pathlib import Path

import fitz

from job_agent.resume_ingestion.ocr import ocr_pdf
from job_agent.resume_ingestion.parsers import ParsedPage, ParsedResume, hash_file


def _extract_native_pages(path: Path) -> list[ParsedPage]:
    with fitz.open(path) as document:
        return [
            ParsedPage(page_number=index + 1, text=page.get_text("text"))
            for index, page in enumerate(document)
        ]


def parse_pdf(path: Path) -> ParsedResume:
    pages = _extract_native_pages(path)
    method = "native_pdf"
    if not any(page.text.strip() for page in pages):
        pages = ocr_pdf(path)
        method = "ocr_pdf"
    if not pages:
        raise ValueError("PDF contains no pages")
    return ParsedResume(
        filename=path.name,
        file_hash=hash_file(path),
        extraction_method=method,
        pages=pages,
    )
