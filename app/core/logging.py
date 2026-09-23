import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Contextvar: el middleware lo setea en cada request
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Campos extra que el middleware inyecta en cada log
_EXTRA_FIELDS = (
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client_ip",
)


class JsonFormatter(logging.Formatter):
    """Formatea cada LogRecord como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id

        for key in _EXTRA_FIELDS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    """Configura logging JSON para toda la app."""
    root = logging.getLogger()
    root.setLevel(level)

    # Elimina handlers previos (evita duplicados al recargar)
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Silencia loggers ruidosos
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
