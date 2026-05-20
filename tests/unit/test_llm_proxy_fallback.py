"""Unit tests for phi_gateway.core.llm_proxy — fallback chain and helpers.

All provider calls are mocked — no real API requests are made.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from phi_gateway.core.llm_proxy import (
    FALLBACK_CHAIN,
    _anthropic_messages,
    _get_client,
    _openai_messages,
    _parse_model,
    _split_system_message,
    _to_openai_message,
    list_models,
    route_chat,
)

# ── FALLBACK_CHAIN structure ──────────────────────────────────────────


class TestFallbackChainStructure:
    def test_fallback_chain_is_dict_with_known_prefixes(self):
        """FALLBACK_CHAIN should be a dict with known provider prefixes."""
        assert isinstance(FALLBACK_CHAIN, dict)
        expected_prefixes = {"anthropic/", "openai/", "groq/", "openrouter/"}
        assert set(FALLBACK_CHAIN.keys()) == expected_prefixes

    def test_fallback_chain_values_are_lists(self):
        """Each fallback chain entry should be a non-empty list of model strings."""
        for prefix, models in FALLBACK_CHAIN.items():
            assert isinstance(models, list), f"{prefix} value should be a list"
            assert len(models) > 0, f"{prefix} should have at least one fallback"
            for m in models:
                assert isinstance(m, str)


# ── _parse_model ──────────────────────────────────────────────────────


class TestParseModel:
    def test_parse_model_with_slash(self):
        """'groq/llama-3.3-70b' → ('groq', 'llama-3.3-70b')."""
        provider, model = _parse_model("groq/llama-3.3-70b")
        assert provider == "groq"
        assert model == "llama-3.3-70b"

    def test_parse_model_without_slash_known(self):
        """'gpt-5-nano' → ('openai', 'gpt-5-nano') via KNOWN_MODELS lookup."""
        provider, model = _parse_model("gpt-5-nano")
        assert provider == "openai"
        assert model == "gpt-5-nano"

    def test_parse_model_without_slash_unknown(self):
        """Unknown model without slash should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            _parse_model("totally-unknown-model")

    def test_parse_model_unknown_provider(self):
        """'unknown/model' should raise ValueError for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            _parse_model("unknown/some-model")


# ── _get_client ───────────────────────────────────────────────────────


class TestGetClient:
    def test_get_client_unknown_provider(self):
        """Unknown provider string should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            _get_client("nonexistent")

    @patch("phi_gateway.core.llm_proxy.settings")
    def test_get_client_missing_api_key(self, mock_settings):
        """Missing API key should raise RuntimeError."""
        mock_settings.OPENAI_API_KEY = None
        with pytest.raises(RuntimeError, match="not available"):
            _get_client("openai")


# ── _split_system_message ─────────────────────────────────────────────


class TestSplitSystemMessage:
    def test_split_system_message_with_system(self):
        """Extracts system message and returns remaining messages."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        system, non_system = _split_system_message(messages)

        assert system == "You are helpful."
        assert len(non_system) == 2
        assert all(m["role"] != "system" for m in non_system)

    def test_split_system_message_without_system(self):
        """Returns (None, all messages) when no system message present."""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        system, non_system = _split_system_message(messages)

        assert system is None
        assert non_system == messages


# ── _to_openai_message ────────────────────────────────────────────────


class TestToOpenAIMessage:
    def test_to_openai_message_list_content(self):
        """Anthropic-style list content blocks are joined into a string."""
        msg = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": "World"},
            ],
        }
        result = _to_openai_message(msg)
        assert result["content"] == "Hello\nWorld"
        assert result["role"] == "assistant"

    def test_to_openai_message_string_content(self):
        """String content passes through unchanged."""
        msg = {"role": "user", "content": "Hi there"}
        result = _to_openai_message(msg)
        assert result["content"] == "Hi there"


# ── Message format helpers ────────────────────────────────────────────


class TestAnthropicMessages:
    def test_anthropic_messages_format(self):
        """Extracts system message and sets max_tokens."""
        messages = [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": "Hello"},
        ]
        result = _anthropic_messages(messages)

        assert result["system"] == "Be brief."
        assert result["max_tokens"] == 4096
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"


class TestOpenAIMessages:
    def test_openai_messages_format(self):
        """Wraps messages under a 'messages' key with OpenAI format."""
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        result = _openai_messages(messages)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "Hello"


# ── list_models ───────────────────────────────────────────────────────


class TestListModels:
    def test_list_models_returns_nonempty_list(self):
        """list_models() returns a non-empty list of dicts with 'id' and 'provider'."""
        models = list_models()
        assert len(models) > 0
        for m in models:
            assert isinstance(m, dict)
            assert "id" in m
            assert "provider" in m


# ── Fallback behaviour in route_chat ─────────────────────────────────


def _make_mock_response(model="fallback-model", provider="groq"):
    """Build a minimal mock OpenAI-style chat completion response."""
    choice = SimpleNamespace(
        index=0,
        message=SimpleNamespace(role="assistant", content="Hello from fallback"),
        finish_reason="stop",
    )
    usage = SimpleNamespace(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )
    return SimpleNamespace(
        id="mock-completion-id",
        created=1700000000,
        choices=[choice],
        usage=usage,
    )


class TestFallbackBehaviour:
    @pytest.mark.asyncio
    async def test_fallback_trigger_on_failure(self):
        """When the primary model fails, the fallback model is tried and succeeds."""
        # Primary model: anthropic/claude-sonnet-4.6  → raises ConnectError
        # Fallback model (from FALLBACK_CHAIN["anthropic/"]): openai/gpt-5.2

        call_log = []  # track which providers were called

        mock_client_fail = AsyncMock()
        mock_client_fail.chat.completions.create = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        mock_client_ok = AsyncMock()
        mock_client_ok.chat.completions.create = AsyncMock(return_value=_make_mock_response())

        def fake_get_client(provider):
            call_log.append(provider)
            if provider == "anthropic":
                return mock_client_fail
            return mock_client_ok

        with patch("phi_gateway.core.llm_proxy._get_client", side_effect=fake_get_client):
            result = await route_chat(
                model="anthropic/claude-sonnet-4.6",
                messages=[{"role": "user", "content": "Hi"}],
            )

        # Should have tried anthropic first, then fallen back
        assert call_log[0] == "anthropic"
        assert len(call_log) >= 2, f"Expected fallback attempt, call_log={call_log}"
        assert result["choices"][0]["message"]["content"] == "Hello from fallback"

    @pytest.mark.asyncio
    async def test_fallback_exhausted_raises_last_error(self):
        """When ALL models in the chain fail, the last error is raised."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=httpx.ConnectError("all down"))

        with patch("phi_gateway.core.llm_proxy._get_client", return_value=mock_client):
            with pytest.raises(httpx.ConnectError, match="all down"):
                await route_chat(
                    model="anthropic/claude-sonnet-4.6",
                    messages=[{"role": "user", "content": "Hi"}],
                )
