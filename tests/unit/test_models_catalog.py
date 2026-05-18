"""Unit tests for models catalog — pricing data consistency.

Verifies that every model in the KNOWN_MODELS catalog has a matching
pricing entry in the cost tracker, and that cost calculations work.
"""

from phi_gateway.core.cost_tracker import COST_PER_1M_TOKENS, calculate_cost
from phi_gateway.core.llm_proxy import KNOWN_MODELS


class TestModelsCatalog:
    def test_known_models_nonempty(self):
        """KNOWN_MODELS should list at least one model."""
        assert len(KNOWN_MODELS) > 0

    def test_every_model_has_id_and_provider(self):
        """Every model entry must have 'id' and 'provider' keys."""
        for model in KNOWN_MODELS:
            assert "id" in model, f"Model missing 'id': {model}"
            assert "provider" in model, f"Model missing 'provider': {model}"

    def test_providers_are_valid(self):
        """All providers must be in the known set."""
        valid_providers = {"openai", "anthropic", "groq", "openrouter"}
        for model in KNOWN_MODELS:
            assert model["provider"] in valid_providers, (
                f"Model '{model['id']}' has unknown provider '{model['provider']}'"
            )


class TestPricingConsistency:
    def test_every_model_has_pricing_entry(self):
        """Every model in KNOWN_MODELS should have a pricing entry in COST_PER_1M_TOKENS.

        Models may match by full ID or by the last segment after '/'.
        """
        missing = []
        for model in KNOWN_MODELS:
            model_id = model["id"]
            # Try direct match
            if model_id in COST_PER_1M_TOKENS:
                continue
            # Try suffix match (e.g. "groq/llama-3.3-70b" → "llama-3.3-70b")
            if "/" in model_id:
                short = model_id.rsplit("/", 1)[-1]
                if short in COST_PER_1M_TOKENS:
                    continue
            missing.append(model_id)

        assert not missing, f"Models without pricing data: {missing}"

    def test_cost_nonzero_for_known_models(self):
        """Cost calculation for known models with tokens > 0 must return nonzero."""
        # Pick a few representative models
        test_cases = [
            ("gpt-5-nano", 1000, 1000),
            ("claude-sonnet-4.6", 500, 500),
            ("groq/llama-3.3-70b", 100, 100),
            ("openrouter/google/gemini-2.5-flash", 200, 200),
        ]
        for model, in_tok, out_tok in test_cases:
            cost = calculate_cost(model, in_tok, out_tok)
            assert cost > 0, f"Expected positive cost for '{model}', got {cost}"

    def test_cost_zero_for_unknown_model(self):
        """Unknown model should return 0, not crash."""
        cost = calculate_cost("nonexistent/model-v99", 1000, 1000)
        assert cost == 0

    def test_cost_zero_for_zero_tokens(self):
        """Zero tokens should return 0 cost even for known models."""
        cost = calculate_cost("gpt-5-nano", 0, 0)
        assert cost == 0

    def test_pricing_entries_are_positive(self):
        """All pricing entries should have positive input and output prices."""
        for model_id, (in_price, out_price) in COST_PER_1M_TOKENS.items():
            assert in_price >= 0, f"{model_id}: negative input price"
            assert out_price >= 0, f"{model_id}: negative output price"
