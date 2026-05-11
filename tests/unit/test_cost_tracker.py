from phi_gateway.core.cost_tracker import calculate_cost


class TestCalculateCost:
    def test_known_model_nano(self):
        """GPT-5-Nano: $0.05/$0.40 per 1M → 1M in + 1M out = $0.45 = 450_000 micro-dollars."""
        cost = calculate_cost("gpt-5-nano", 1_000_000, 1_000_000)
        assert cost == 450000, f"Expected 450000, got {cost}"

    def test_known_model_mini(self):
        """GPT-5-Mini: $0.25/$2.00 per 1M → 1M in + 500K out = $0.25 + $1.00 = $1.25."""
        cost = calculate_cost("gpt-5-mini", 1_000_000, 500_000)
        assert cost == 1250000, f"Expected 1250000, got {cost}"

    def test_known_model_groq(self):
        """Groq model (suffix match): should resolve through /-delimited model name."""
        cost = calculate_cost("groq/llama-3.3-70b", 1000, 500)
        assert cost > 0, f"Expected positive cost, got {cost}"

    def test_unknown_model_returns_zero(self):
        """Unknown model should return 0 and not crash."""
        cost = calculate_cost("completely-unknown-model", 1000, 1000)
        assert cost == 0, f"Expected 0, got {cost}"

    def test_zero_tokens_returns_zero(self):
        """Zero tokens should return 0 cost."""
        cost = calculate_cost("gpt-5-nano", 0, 0)
        assert cost == 0, f"Expected 0, got {cost}"
