from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ParsedPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    page_number: int = Field(ge=1)
    text: str


class ParsedResume(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    filename: str
    file_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    extraction_method: str
    pages: list[ParsedPage]

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)


class UnsupportedResumeFormat(ValueError):
    pass


class ResumeParser:
    def parse(self, path: Path) -> ParsedResume:
        if not path.is_file():
            raise FileNotFoundError(path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            from job_agent.resume_ingestion.pdf_parser import parse_pdf

            return parse_pdf(path)
        if suffix == ".docx":
            from job_agent.resume_ingestion.docx_parser import parse_docx

            return parse_docx(path)
        if suffix in {".txt", ".md"}:
            from job_agent.resume_ingestion.text_parser import parse_text

            return parse_text(path)
        raise UnsupportedResumeFormat(f"unsupported resume format: {suffix}")


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
