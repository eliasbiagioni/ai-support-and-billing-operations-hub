"""LLM client abstraction (PRD 7.3).

Real-only integration: ``OpenAILLMClient`` talks to the OpenAI API and requires
``OPENAI_API_KEY``. Tests override the ``get_llm_client`` dependency with a fake
so no network calls happen in CI.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings
from app.core.errors import AppError


class LLMConfigError(AppError):
    """Raised when the LLM is invoked without the required configuration."""

    status_code = 503
    code = "llm_unavailable"


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        """Return the model's text completion for the given prompt."""
        ...


class OpenAILLMClient:
    """Thin wrapper over the OpenAI Chat Completions API."""

    def __init__(self, *, api_key: str, model: str) -> None:
        if not api_key:
            raise LLMConfigError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY to use AI features."
            )
        # Imported lazily so the package is only required when AI features run.
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        kwargs: dict[str, object] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = self._client.chat.completions.create(**kwargs)  # type: ignore[arg-type]
        return response.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    """FastAPI dependency returning the configured LLM client.

    Raises ``LLMConfigError`` (503) when no API key is present, so AI endpoints
    fail clearly while the rest of the app keeps working without keys.
    """

    return OpenAILLMClient(api_key=settings.OPENAI_API_KEY, model=settings.AI_MODEL)
