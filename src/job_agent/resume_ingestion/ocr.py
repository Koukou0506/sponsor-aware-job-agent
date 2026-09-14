from pathlib import Path

import fitz

from job_agent.resume_ingestion.parsers import ParsedPage


class OcrUnavailable(RuntimeError):
    pass


def ocr_pdf(path: Path, languages: str = "eng+chi_sim") -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    try:
        with fitz.open(path) as document:
            for index, page in enumerate(document):
                text_page = page.get_textpage_ocr(language=languages, dpi=300, full=True)
                pages.append(
                    ParsedPage(
                        page_number=index + 1,
                        text=page.get_text("text", textpage=text_page),
                    )
                )
    except RuntimeError as exc:
        raise OcrUnavailable(
            "OCR requires a local Tesseract installation with eng and chi_sim language data"
        ) from exc
    if not any(page.text.strip() for page in pages):
        raise OcrUnavailable("OCR completed but produced no text")
    return pages
