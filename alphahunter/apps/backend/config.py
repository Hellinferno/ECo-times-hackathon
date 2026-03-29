from __future__ import annotations

import re
import warnings
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    # ── Database ───────────────────────────────────────────────────────────────
    # Set DATABASE_URL directly (e.g. Railway postgres:// URL) to bypass the
    # individual DB_* fields.  Leave blank to use the component-based fallback.
    DB_USER: str = "alphahunter"
    DB_PASSWORD: str = "alpha123"
    DB_NAME: str = "alphahunter_dev"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DATABASE_URL: str | None = None

    # ── Redis ──────────────────────────────────────────────────────────────────
    # Set REDIS_URL directly for hosted Redis (e.g. rediss://...).
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str | None = None

    # ── CORS ───────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.  Wildcard subdomain patterns
    # (e.g. https://*.vercel.app) are supported via allow_origin_regex.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://*.vercel.app"

    # ── LLM (Gemini) ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_MAX_TOKENS: int = 1024
    LLM_TIMEOUT_SECS: int = 30

    # ── External APIs (TinyFish / Mino) ────────────────────────────────────────
    MINO_API_KEY: str = ""
    TINYFISH_RUN_SSE_URL: str = "https://mino.ai/v1/automation/run-sse"
    TINYFISH_DEFAULT_TIMEOUT_SECS: int = 20

    # ── Auth / JWT ─────────────────────────────────────────────────────────────
    AUTH_JWT_SECRET: str = "alphahunter-demo-jwt-secret-change-me"
    AUTH_JWT_EXPIRE_MINUTES: int = 480
    AUTH_DEMO_PASSWORD: str = "AlphaHunter-demo-2026!"
    AUTH_DEMO_ORG_SLUG: str = "alphahunter-labs"
    AUTH_DEMO_ORG_NAME: str = "AlphaHunter Labs"

    # ── Alerts — Telegram ──────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # ── Misc ───────────────────────────────────────────────────────────────────
    WORLDMONITOR_API_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file="../../../.env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _warn_insecure_defaults(self) -> "Settings":
        _DEFAULT_JWT = "alphahunter-demo-jwt-secret-change-me"
        if self.APP_ENV != "development" and self.AUTH_JWT_SECRET == _DEFAULT_JWT:
            warnings.warn(
                "AUTH_JWT_SECRET is using the default demo value in a non-development environment. "
                "Set a strong random secret in your .env file before deploying.",
                stacklevel=2,
            )
        return self

    # ── Computed properties ────────────────────────────────────────────────────

    @staticmethod
    def _normalize_database_url(url: str) -> str:
        """Rewrite legacy postgres:// scheme to SQLAlchemy-compatible postgresql://."""
        normalized = url.strip()
        if normalized.startswith("postgres://"):
            return f"postgresql://{normalized[len('postgres://'):]}"
        return normalized

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self._normalize_database_url(self.DATABASE_URL)

        # Fallback to SQLite for local rapid dev without Docker
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
        """Exact-match origins (no wildcards) passed to CORSMiddleware allow_origins."""
        origins: list[str] = []
        for value in self.ALLOWED_ORIGINS.split(","):
            origin = value.strip().rstrip("/")
            if not origin or "*" in origin:
                continue
            origins.append(origin)
        return origins

    @property
    def allowed_origin_regex(self) -> str | None:
        """
        Regex for wildcard origins passed to CORSMiddleware allow_origin_regex.

        Uses [^./]+ (no dots, no slashes) so that https://*.vercel.app matches
        exactly one subdomain segment — preventing https://evil.also.vercel.app
        from matching via regex backtracking.
        """
        wildcard_patterns: list[str] = []
        for value in self.ALLOWED_ORIGINS.split(","):
            origin = value.strip().rstrip("/")
            if not origin or "*" not in origin:
                continue
            # Replace escaped \* with a single-segment wildcard (no dots, no slashes)
            pattern = re.escape(origin).replace(r"\*", r"[^./]+")
            wildcard_patterns.append("^" + pattern + "$")

        if not wildcard_patterns:
            return None

        return "|".join(wildcard_patterns)


settings = Settings()
