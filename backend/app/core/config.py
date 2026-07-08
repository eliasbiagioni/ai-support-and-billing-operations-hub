"""Application configuration loaded from environment variables.

Uses Pydantic v2 settings so the same typed contract validates the environment in
local dev, Docker, and CI. Stripe/LLM keys are declared here so later phases can
consume them without touching the config surface again.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Core
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-secret-change-me"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/supportledger"

    # CORS. NoDecode disables pydantic-settings' JSON decoding so a plain
    # comma-separated env string is accepted (parsed by the validator below).
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # External integrations (unused until later phases, declared for a stable contract)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return value
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
