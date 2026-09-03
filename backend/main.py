import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from core.db import safe_db_url
from core.logging_config import setup_logging

log = logging.getLogger("overseer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    # Schema is owned by Alembic (`alembic upgrade head`), NOT by the app.
    log.info("Starting Overseer (env=%s, db=%s)", settings.APP_ENV, safe_db_url())
    yield
    log.info("Shutting down Overseer")


app = FastAPI(title="The Overseer", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}
