from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
