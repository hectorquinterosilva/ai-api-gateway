import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

_EXTRA_FIELDS = (
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client_ip",
)

# Loggers que uvicorn/gunicorn crean y que hay que redirigir a JSON
_OVERRIDE_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "gunicorn",
    "gunicorn.error",
    "gunicorn.access",
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
    """Configura logging JSON para toda la app, incluido uvicorn."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)

    # Sobreescribe loggers de uvicorn/gunicorn para que usen el mismo handler
    for name in _OVERRIDE_LOGGERS:
        lg = logging.getLogger(name)
        for h in lg.handlers[:]:
            lg.removeHandler(h)
        lg.handlers = [handler]
        lg.propagate = False
        lg.setLevel(level)

    # Silencia loggers ruidosos (ya loggeamos nosotros con el middleware)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
