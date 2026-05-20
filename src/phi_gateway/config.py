"""Application configuration via environment variables and .env file.

Loaded automatically on import via pydantic-settings.
Access settings globally through the ``settings`` singleton.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the PhiGateway application.

    Reads from ``.env`` file and environment variables, with ``.env``
    taking precedence over system environment variables. Unknown extra
    fields are silently ignored.

    Attributes:
        DATABASE_URL: Async SQLAlchemy connection string.
            Defaults to SQLite at ``data/phi.db``.
        OPENAI_API_KEY: Optional OpenAI API key.
        ANTHROPIC_API_KEY: Optional Anthropic API key.
        GROQ_API_KEY: Optional Groq API key.
        OPENROUTER_API_KEY: Optional OpenRouter API key.
        APP_HOST: Host interface to bind the server to.
        APP_PORT: Port to listen on.
        ALLOWED_ORIGINS: Comma-separated CORS origins or ``"*"`` for all.
        MAX_REQUEST_BODY_SIZE: Maximum request body size in bytes (10 MB default).
        INITIAL_ADMIN_KEY: Optional bootstrap admin API key for first deploy.
        SESSION_SECRET: Secret key for cookie-based dashboard sessions.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///data/phi.db"

    # LLM Providers (optional — only configure the ones you use)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # App
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # Security
    ALLOWED_ORIGINS: str = "*"  # comma-separated list or "*" for all
    MAX_REQUEST_BODY_SIZE: int = 10 * 1024 * 1024  # 10 MB default

    # Bootstrap admin API key (set on first deploy to seed the first key)
    INITIAL_ADMIN_KEY: str | None = None

    # Session secret for cookie-based dashboard auth
    SESSION_SECRET: str = "change-me-in-production"


settings = Settings()
"""Global settings instance, initialized at import time."""
