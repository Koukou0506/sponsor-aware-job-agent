from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from job_agent.resume_ingestion.parsers import ParsedResume


class ExtractedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractedBullet(ExtractedModel):
    category: str
    organisation: str | None = None
    role_or_project: str | None = None
    original_text: str
    action: str | None = None
    method: str | None = None
    object: str | None = None
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    outcome: str | None = None
    source_id: str
    page_number: int | None = None
    section: str
    confidence: float = Field(ge=0, le=1)


class ExtractedBasicInfo(ExtractedModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None


class ExtractedEducation(ExtractedModel):
    institution: str
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    ranking: str | None = None
    coursework: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)


class ExtractedExperience(ExtractedModel):
    organisation: str
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)


class ExtractedProject(ExtractedModel):
    name: str
    organisation: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)


class ExtractedLanguage(ExtractedModel):
    language: str
    level: str | None = None
    certificate: str | None = None


class ExtractedResume(ExtractedModel):
    language: Literal["en", "zh", "mixed", "unknown"]
    resume_track: Literal["technical", "technical_business", "historical", "unknown"]
    basic_info: ExtractedBasicInfo = Field(default_factory=ExtractedBasicInfo)
    education: list[ExtractedEducation] = Field(default_factory=list)
    experiences: list[ExtractedExperience] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    languages: list[ExtractedLanguage] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    bullets: list[ExtractedBullet] = Field(default_factory=list)


class ResumeExtractionProvider(Protocol):
    def extract(self, parsed: ParsedResume, source_id: str) -> ExtractedResume: ...


class HeuristicResumeExtractor:
    _HEADINGS = {
        "education": "education",
        "教育经历": "education",
        "experience": "experience",
        "work experience": "experience",
        "internship experience": "experience",
        "实习经历": "experience",
        "projects": "projects",
        "selected projects": "projects",
        "项目经历": "projects",
        "skills": "skills",
        "技能": "skills",
        "languages": "languages",
        "语言能力": "languages",
    }

    def extract(self, parsed: ParsedResume, source_id: str) -> ExtractedResume:
        section = "unknown"
        bullets: list[ExtractedBullet] = []
        skills: list[str] = []
        for page in parsed.pages:
            for raw_line in page.text.splitlines():
                line = raw_line.strip(" •-\t")
                if not line:
                    continue
                heading = self._HEADINGS.get(line.casefold())
                if heading:
                    section = heading
                    continue
                if section == "skills":
                    skills.extend(
                        item.strip()
                        for item in line.replace("；", ";").split(";")
                        if item.strip()
                    )
                    continue
                bullets.append(
                    ExtractedBullet(
                        category="project" if section == "projects" else "experience",
                        original_text=line,
                        outcome=line,
                        source_id=source_id,
                        page_number=page.page_number,
                        section=section,
                        confidence=0.55,
                    )
                )
        contains_chinese = any("\u4e00" <= char <= "\u9fff" for char in parsed.text)
        contains_latin = any(char.isascii() and char.isalpha() for char in parsed.text)
        language: Literal["en", "zh", "mixed", "unknown"]
        if contains_chinese and contains_latin:
            language = "mixed"
        elif contains_chinese:
            language = "zh"
        elif contains_latin:
            language = "en"
        else:
            language = "unknown"
        return ExtractedResume(
            language=language,
            resume_track="unknown",
            skills=skills,
            bullets=bullets,
        )
