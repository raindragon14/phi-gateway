from phi_gateway.core.security import generate_api_key, verify_api_key


class TestGenerateApiKey:
    def test_key_format(self):
        """Key starts with phi-sk- and has correct total length."""
        full, prefix, hashed = generate_api_key()
        assert full.startswith("phi-sk-"), f"Key should start with 'phi-sk-', got '{full[:10]}'"
        # phi-sk- = 7 chars + 48 hex = 55 total
        assert len(full) == 55, f"Key should be 55 chars, got {len(full)}"

    def test_prefix_is_first_12_chars(self):
        """Prefix matches first 12 characters of the full key."""
        full, prefix, hashed = generate_api_key()
        assert prefix == full[:12], f"Prefix '{prefix}' should match '{full[:12]}'"

    def test_hashed_is_bcrypt(self):
        """Hash string starts with bcrypt prefix."""
        _, _, hashed = generate_api_key()
        assert hashed.startswith("$2b$"), f"Hash should start with '$2b$', got '{hashed[:4]}'"


class TestVerifyApiKey:
    def test_valid_key(self):
        """A generated key should verify against its hash."""
        full, _, hashed = generate_api_key()
        assert verify_api_key(full, hashed) is True

    def test_invalid_key(self):
        """A wrong key should return False, not raise."""
        full, _, hashed = generate_api_key()
        assert verify_api_key("wrong-key", hashed) is False

    def test_invalid_hash_format(self):
        """Malformed hash should return False, not raise."""
        assert verify_api_key("any-key", "not-a-valid-hash") is False

    def test_empty_key(self):
        """Empty string should not crash."""
        full, _, hashed = generate_api_key()
        assert verify_api_key("", hashed) is False
