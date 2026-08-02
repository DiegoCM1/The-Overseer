import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from core.db import safe_db_url
from core.logging_config import setup_logging
from core.scheduler import start_scheduler, stop_scheduler
from features.monitor.models import Notification  # noqa: F401  (registers the table)
from features.monitor.service import tick
from features.voice.router import router as voice_router

log = logging.getLogger("overseer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    setup_logging(settings.LOG_LEVEL)

    # Schema is owned by Alembic (`alembic upgrade head`), NOT by the app.
    # create_all() used to run here; it was blocking DDL on the event loop and it
    # could only ever CREATE, never ALTER — so any column change silently drifted.
    log.info("Starting Overseer (env=%s, db=%s)", settings.APP_ENV, safe_db_url())

    start_scheduler()
    try:
        yield
    finally:
        # SHUTDOWN — in `finally` so the scheduler is stopped even if startup
        # or the app body raises. A leaked scheduler thread keeps firing Twilio.
        log.info("Shutting down Overseer")
        stop_scheduler()


app = FastAPI(title="The Overseer", lifespan=lifespan)
app.include_router(voice_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


# Dev-only manual trigger so you can fire a poll without waiting for the heartbeat.
if settings.APP_ENV == "dev":

    @app.post("/debug/tick")
    async def debug_tick():
        await tick()
        return {"ok": True}
