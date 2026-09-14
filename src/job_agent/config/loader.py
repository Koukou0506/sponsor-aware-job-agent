from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

from job_agent.config.models import (
    CandidateProfileConfig,
    PreferencesConfig,
    ScoringRulesConfig,
    VisaAnswersConfig,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


def _load_yaml(path: Path, model_type: type[ModelT]) -> ModelT:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return model_type.model_validate(payload)


class ConfigBundle(BaseModel):
    profile: CandidateProfileConfig
    preferences: PreferencesConfig
    visa_answers: VisaAnswersConfig
    scoring_rules: ScoringRulesConfig

    @classmethod
    def load(cls, directory: Path) -> "ConfigBundle":
        return cls(
            profile=_load_yaml(directory / "profile.yaml", CandidateProfileConfig),
            preferences=_load_yaml(directory / "preferences.yaml", PreferencesConfig),
            visa_answers=_load_yaml(directory / "visa_answers.yaml", VisaAnswersConfig),
            scoring_rules=_load_yaml(directory / "scoring_rules.yaml", ScoringRulesConfig),
        )
