"""The heartbeat. An in-process APScheduler runs the Overseer tick on an interval,
started/stopped with the FastAPI app lifespan.

A scheduled job that dies silently is the worst failure mode this system has: the
process stays up, health checks stay green, and nothing is ever sent. So every job
error and every missed run is logged explicitly with a traceback.
"""

import logging

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import settings
from features.monitor.service import tick

log = logging.getLogger("overseer")

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)


def _on_job_event(event) -> None:
    if event.code == EVENT_JOB_ERROR:
        # exc_info gives us the traceback from inside the job, which APScheduler
        # would otherwise swallow into its own logger at a level nobody reads.
        log.error(
            "Scheduled job %r raised: %s",
            event.job_id,
            event.exception,
            exc_info=(type(event.exception), event.exception, event.traceback),
        )
    elif event.code == EVENT_JOB_MISSED:
        log.warning(
            "Scheduled job %r MISSED its run at %s (event loop blocked or process stalled)",
            event.job_id,
            event.scheduled_run_time,
        )


def start_scheduler() -> None:
    scheduler.add_job(
        tick,
        "interval",
        minutes=settings.POLL_MINUTES,
        id="overseer_tick",
        replace_existing=True,
        coalesce=True,          # collapse missed runs into one
        max_instances=1,        # never overlap ticks
        misfire_grace_time=300,  # a run up to 5 min late still counts; older is reported
    )
    scheduler.add_listener(_on_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    scheduler.start()

    job = scheduler.get_job("overseer_tick")
    log.info(
        "Overseer heartbeat started (every %d min, tz=%s, next run %s)",
        settings.POLL_MINUTES,
        settings.TIMEZONE,
        getattr(job, "next_run_time", "unknown"),
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("Overseer heartbeat stopped")
