from typing import Protocol, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class StructuredLlm(Protocol):
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT: ...


class FixtureStructuredLlm:
    def __init__(self, fixtures: dict[str, object]) -> None:
        self._fixtures = fixtures

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT:
        del system_prompt
        return response_model.model_validate(self._fixtures[user_prompt])
