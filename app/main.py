"""FastAPI entrypoint for ClusterSage.

The API surface is intentionally light. It exists to support health checks and
future orchestration of the batch-oriented triage pipeline, not to hide the
core logic behind a large service layer.
"""

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Light API surface for ClusterSage services and future orchestration.",
    version="0.1.0",
)
app.include_router(router)
