from typing import Any, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class OpenAiStructuredLlm:
    def __init__(self, model: str, client: Any | None = None) -> None:
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "Install the llm optional dependency to use OpenAI"
                ) from exc
            client = OpenAI()
        self._model = model
        self._client = client

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT:
        response = self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=response_model,
        )
        if response.output_parsed is None:
            raise ValueError("structured model response was empty")
        return response_model.model_validate(response.output_parsed)
