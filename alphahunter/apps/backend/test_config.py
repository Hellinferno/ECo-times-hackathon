import re

from config import Settings


def test_settings_prefer_hosted_urls(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@db.example.com:5432/alphahunter")
    monkeypatch.setenv("REDIS_URL", "rediss://cache.example.com:6379/0")
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173, https://alphahunter.app, https://*.vercel.app",
    )

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql://user:pass@db.example.com:5432/alphahunter"
    assert settings.redis_url == "rediss://cache.example.com:6379/0"
    assert settings.parsed_allowed_origins == [
        "http://localhost:5173",
        "https://alphahunter.app",
    ]
    assert settings.allowed_origin_regex is not None
    # Legitimate single-segment subdomain must match
    assert re.match(settings.allowed_origin_regex, "https://preview-123.vercel.app")
    # Completely unrelated domain must not match
    assert not re.match(settings.allowed_origin_regex, "https://evil.other.app")
    # Trailing domain suffix attack must not match
    assert not re.match(settings.allowed_origin_regex, "https://preview-123.vercel.app.evil.com")
    # Multi-segment subdomain attack must not match (was vulnerable with [^/]+)
    assert not re.match(settings.allowed_origin_regex, "https://deep.sub.vercel.app")


def test_settings_keep_local_dev_fallbacks(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "alphahunter_dev")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./alphahunter_dev.db"
    assert settings.redis_url == "redis://localhost:6379"
