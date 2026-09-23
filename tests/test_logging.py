"""Tests de logging estructurado y middleware de request ID."""
import json
import logging

from app.core.logging import JsonFormatter, request_id_ctx


def test_json_formatter_basic():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello world",
        args=(),
        exc_info=None,
    )
    out = JsonFormatter().format(record)
    data = json.loads(out)

    assert data["level"] == "INFO"
    assert data["logger"] == "test"
    assert data["message"] == "hello world"
    assert "timestamp" in data


def test_json_formatter_extra_fields():
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.method = "POST"
    record.path = "/users"
    record.status_code = 409
    record.duration_ms = 12.5
    record.client_ip = "127.0.0.1"

    data = json.loads(JsonFormatter().format(record))

    assert data["method"] == "POST"
    assert data["path"] == "/users"
    assert data["status_code"] == 409
    assert data["duration_ms"] == 12.5
    assert data["client_ip"] == "127.0.0.1"


def test_json_formatter_includes_request_id():
    token = request_id_ctx.set("abc-123")
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="x",
            args=(),
            exc_info=None,
        )
        data = json.loads(JsonFormatter().format(record))
        assert data["request_id"] == "abc-123"
    finally:
        request_id_ctx.reset(token)


# ============================================================
# Middleware
# ============================================================
def test_response_includes_request_id(client):
    r = client.get("/health")
    assert "X-Request-ID" in r.headers
    # Un UUID v4 tiene 36 caracteres
    assert len(r.headers["X-Request-ID"]) == 36


def test_response_echoes_client_request_id(client):
    rid = "custom-request-id-xyz"
    r = client.get("/health", headers={"X-Request-ID": rid})
    assert r.headers["X-Request-ID"] == rid
