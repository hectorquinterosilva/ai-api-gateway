from fastapi import FastAPI

from app.db.base import Base
from app.db.database import engine

import app.models.user

from app.api.users import router as users_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI API Gateway",
    version="0.1.0"
)

app.include_router(
    users_router
)


@app.get("/")
def root():

    return {
        "service": "AI API Gateway",
        "status": "running"
    }
