"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.observability import configure_logging, request_observability_middleware
from app.seed import initialize_schema, seed_demo_dataset


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_schema()
    if settings.seed_demo_on_startup:
        seed_demo_dataset()
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    if settings.observability_enabled:
        app.middleware("http")(request_observability_middleware)
    app.include_router(router)
    return app


app = create_app()
