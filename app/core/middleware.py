import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger("app.request")

_METRICS_EXCLUDED = ("/metrics",)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        client_ip = request.client.host if request.client else None
        start = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                },
            )
            request_id_ctx.reset(token)
            raise

        duration_s = time.perf_counter() - start
        duration_ms = duration_s * 1000
        response.headers["X-Request-ID"] = request_id

        if response.status_code >= 500:
            level = logging.ERROR
        elif response.status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        logger.log(
            level,
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            },
        )

        if request.url.path not in _METRICS_EXCLUDED:
            REQUEST_COUNT.labels(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            ).inc()
            REQUEST_LATENCY.labels(
                method=request.method,
                path=request.url.path,
            ).observe(duration_s)

        request_id_ctx.reset(token)
        return response
