import redis

from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def check_redis() -> bool:
    """Devuelve True si Redis responde a PING."""
    try:
        redis_client.ping()
        return True
    except Exception:
        return False
