from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.users import router as users_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.redis import check_redis
from app.db.session import engine

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(RequestIDMiddleware)
app.include_router(users_router)


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


def _check_database() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    checks = {
        "database": _check_database(),
        "redis": check_redis(),
    }
    all_ok = all(checks.values())
    payload = {
        "status": "ok" if all_ok else "degraded",
        "version": settings.APP_VERSION,
        "checks": {k: ("ok" if v else "error") for k, v in checks.items()},
    }
    status_code = 200 if all_ok else 503
    return JSONResponse(content=payload, status_code=status_code)
