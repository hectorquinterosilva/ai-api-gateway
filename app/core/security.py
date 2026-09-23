import hashlib
import secrets

API_KEY_PREFIX = "aigw_"


def generate_api_key() -> str:
    """Genera una API key en claro. Solo se muestra una vez al usuario."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(plain: str) -> str:
    """
    SHA-256 hex.

    Las API keys son de alta entropía (32 bytes random), por lo que no
    necesitan un hash lento tipo bcrypt. SHA-256 es rápido, determinista
    y suficiente. El campo api_key_hash en BD guarda este hex.
    """
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()
