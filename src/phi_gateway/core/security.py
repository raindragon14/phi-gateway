import secrets

import bcrypt

KEY_PREFIX = "phi-sk"
KEY_LENGTH = 48  # hex chars after prefix


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns:
        Tuple of (full_key, prefix, bcrypt_hash).
        Full key format: phi-sk-<48 random hex chars>
        Prefix: first 12 chars of full key (for display/lookup)
    """
    raw = secrets.token_hex(KEY_LENGTH // 2)  # 48 hex chars = 24 bytes
    full_key = f"{KEY_PREFIX}-{raw}"
    prefix = full_key[:12]
    hashed = bcrypt.hashpw(full_key.encode(), bcrypt.gensalt()).decode()
    return full_key, prefix, hashed


def verify_api_key(plain_key: str, hashed: str) -> bool:
    """Verify a plain-text API key against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_key.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False
