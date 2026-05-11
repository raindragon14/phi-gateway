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


def hash_key(key: str) -> str:
    """Hash a key for storage (used when key is not freshly generated)."""
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


def extract_prefix(key: str) -> str:
    """Extract the display prefix from a full API key."""
    return key[:12]
