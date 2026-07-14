"""LLM client abstraction (PRD 7.3).

Real-only integration: ``OpenAILLMClient`` talks to the OpenAI API and requires
``OPENAI_API_KEY``. Tests override the ``get_llm_client`` dependency with a fake
so no network calls happen in CI.

Exposes three capabilities:
- ``complete``: single-shot text/JSON completion (AI Assist v1).
- ``chat``: multi-turn tool-calling loop primitive (Phase 5 copilot).
- ``embed``: text embeddings for semantic search (Phase 6 RAG).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import settings
from app.core.errors import AppError


class LLMConfigError(AppError):
    """Raised when the LLM is invoked without the required configuration."""

    status_code = 503
    code = "llm_unavailable"


@dataclass(frozen=True)
class ToolCall:
    """A single tool/function call requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatResult:
    """Result of one ``chat`` turn: free-text content and/or tool calls."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    def as_assistant_message(self) -> dict[str, Any]:
        """Serialize back to an OpenAI assistant message for the next turn."""

        message: dict[str, Any] = {"role": "assistant", "content": self.content or ""}
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                }
                for call in self.tool_calls
            ]
        return message


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        """Return the model's text completion for the given prompt."""
        ...

    def chat(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResult:
        """Run one chat turn, optionally exposing tools for the model to call."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return an embedding vector for each input text."""
        ...


class OpenAILLMClient:
    """Thin wrapper over the OpenAI Chat Completions + Embeddings APIs."""

    def __init__(self, *, api_key: str, model: str, embedding_model: str) -> None:
        if not api_key:
            raise LLMConfigError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY to use AI features."
            )
        # Imported lazily so the package is only required when AI features run.
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model

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

    def chat(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResult:
        kwargs: dict[str, object] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        response = self._client.chat.completions.create(**kwargs)  # type: ignore[arg-type]
        message = response.choices[0].message
        tool_calls: list[ToolCall] = []
        for call in message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(
                ToolCall(id=call.id, name=call.function.name, arguments=arguments)
            )
        return ChatResult(content=message.content, tool_calls=tool_calls)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(
            model=self._embedding_model, input=texts
        )
        return [item.embedding for item in response.data]


def get_llm_client() -> LLMClient:
    """FastAPI dependency returning the configured LLM client.

    Raises ``LLMConfigError`` (503) when no API key is present, so AI endpoints
    fail clearly while the rest of the app keeps working without keys.
    """

    return OpenAILLMClient(
        api_key=settings.OPENAI_API_KEY,
        model=settings.AI_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
    )


def get_optional_llm_client() -> LLMClient | None:
    """Return an LLM client if configured, else ``None``.

    Used where AI is an enhancement rather than a requirement (e.g. computing
    embeddings when creating knowledge articles) so those endpoints keep working
    without an API key.
    """

    if not settings.OPENAI_API_KEY:
        return None
    return get_llm_client()
