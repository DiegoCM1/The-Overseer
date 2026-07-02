"""The heartbeat. An in-process APScheduler runs the Overseer tick on an interval,
started/stopped with the FastAPI app lifespan."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import settings
from features.monitor.service import tick

log = logging.getLogger("overseer")

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)


def start_scheduler() -> None:
    scheduler.add_job(
        tick,
        "interval",
        minutes=settings.POLL_MINUTES,
        id="overseer_tick",
        replace_existing=True,
        coalesce=True,          # collapse missed runs into one
        max_instances=1,        # never overlap ticks
    )
    scheduler.start()
    log.info("Overseer heartbeat started (every %d min)", settings.POLL_MINUTES)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
