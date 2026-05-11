from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///data/phi.db"

    # LLM Providers (optional — only configure the ones you use)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000


settings = Settings()
