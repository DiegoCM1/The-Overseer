import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from core.db import Base, engine
from core.scheduler import start_scheduler, stop_scheduler
from features.monitor.models import Notification  # noqa: F401  (registers the table)
from features.monitor.service import tick
from features.tasks.models import Tasks  # noqa: F401  (registers the table)
from features.voice.router import router as voice_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("🟢 Initializing resources...")
    Base.metadata.create_all(engine)
    print("Created all tables in db")
    start_scheduler()
    yield
    # SHUTDOWN
    print("🔴 Shutting down...")
    stop_scheduler()


app = FastAPI(lifespan=lifespan)
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
