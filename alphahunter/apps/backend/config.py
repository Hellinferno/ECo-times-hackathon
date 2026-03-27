from __future__ import annotations

import re
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = "alphahunter"
    DB_PASSWORD: str = "alpha123"
    DB_NAME: str = "alphahunter_dev"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DATABASE_URL: str | None = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str | None = None

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://*.vercel.app"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_MAX_TOKENS: int = 250
    LLM_TIMEOUT_SECS: int = 30

    MINO_API_KEY: str = ""
    TINYFISH_RUN_SSE_URL: str = "https://mino.ai/v1/automation/run-sse"
    TINYFISH_DEFAULT_TIMEOUT_SECS: int = 20

    model_config = SettingsConfigDict(
        env_file="../../../.env",
        extra="ignore",
    )

    @staticmethod
    def _normalize_database_url(url: str) -> str:
        normalized = url.strip()
        if normalized.startswith("postgres://"):
            return f"postgresql://{normalized[len('postgres://'):]}"
        return normalized

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self._normalize_database_url(self.DATABASE_URL)

        # Fallback to sqlite if host is localhost to aid local rapid dev without docker
        if self.DB_HOST == "localhost" and self.DB_NAME == "alphahunter_dev":
            return "sqlite:///./alphahunter_dev.db"

        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL.strip()
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def parsed_allowed_origins(self) -> list[str]:
        origins: list[str] = []
        for value in self.ALLOWED_ORIGINS.split(","):
            origin = value.strip().rstrip("/")
            if not origin or "*" in origin:
                continue
            origins.append(origin)
        return origins

    @property
    def allowed_origin_regex(self) -> str | None:
        wildcard_patterns: list[str] = []
        for value in self.ALLOWED_ORIGINS.split(","):
            origin = value.strip().rstrip("/")
            if not origin or "*" not in origin:
                continue
            pattern = re.escape(origin).replace(r"\*", r"[^/]+")
            wildcard_patterns.append("^" + pattern + "$")

        if not wildcard_patterns:
            return None

        return "|".join(wildcard_patterns)


settings = Settings()
