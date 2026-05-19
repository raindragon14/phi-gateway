"""Unit tests for phi_gateway.config — Settings class defaults."""

from phi_gateway.config import Settings


class TestSettingsDefaults:
    def test_default_database_url(self):
        """DATABASE_URL defaults to SQLite."""
        s = Settings(_env_file=None)
        assert "sqlite" in s.DATABASE_URL

    def test_default_app_host(self):
        """APP_HOST defaults to 127.0.0.1 (safe for local dev; Docker overrides via compose)."""
        s = Settings(_env_file=None)
        assert s.APP_HOST == "127.0.0.1"

    def test_default_app_port(self):
        """APP_PORT defaults to 8000."""
        s = Settings(_env_file=None)
        assert s.APP_PORT == 8000

    def test_default_allow_origins_is_star(self):
        """ALLOWED_ORIGINS defaults to '*'."""
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == "*"

    def test_default_max_body_size(self):
        """MAX_REQUEST_BODY_SIZE defaults to 10 MB (10 * 1024 * 1024)."""
        s = Settings(_env_file=None)
        assert s.MAX_REQUEST_BODY_SIZE == 10 * 1024 * 1024

    def test_default_api_keys_are_none(self):
        """LLM provider API keys default to None."""
        s = Settings(_env_file=None)
        assert s.OPENAI_API_KEY is None
        assert s.ANTHROPIC_API_KEY is None
        assert s.GROQ_API_KEY is None
        assert s.OPENROUTER_API_KEY is None
