from pathlib import Path

from job_agent.resume_ingestion.parsers import ParsedPage, ParsedResume, hash_file


def parse_text(path: Path) -> ParsedResume:
    return ParsedResume(
        filename=path.name,
        file_hash=hash_file(path),
        extraction_method="markdown" if path.suffix.lower() == ".md" else "text",
        pages=[ParsedPage(page_number=1, text=path.read_text(encoding="utf-8"))],
    )
