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
from features.enforcement import judge
from features.enforcement.service import run_heartbeat, run_judgment, run_reminder
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
    # ---- The bet ----------------------------------------------------------- #
    # Cron times are LOCAL (the scheduler's timezone is settings.TIMEZONE) and are
    # taken from judge.py so the schedule can never drift away from the contract
    # the judge enforces.
    scheduler.add_job(
        run_reminder,
        "cron",
        day_of_week="mon-fri",
        hour=judge.REMINDER.hour,
        minute=judge.REMINDER.minute,
        id="bet_reminder",
        replace_existing=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        run_judgment,
        "cron",
        day_of_week="mon-fri",
        hour=judge.DEADLINE.hour,
        minute=judge.DEADLINE.minute,
        id="bet_judgment",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        # Generous: a judgment that runs late is still correct (the verdict is a
        # function of stored evidence, not of when the job happened to fire), and
        # a skipped judgment would silently gift Diego the day.
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        run_heartbeat,
        "cron",
        hour=settings.HEARTBEAT_HOUR,
        minute=0,
        id="bet_heartbeat",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_listener(_on_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    scheduler.start()

    for job_id in ("overseer_tick", "bet_reminder", "bet_judgment", "bet_heartbeat"):
        job = scheduler.get_job(job_id)
        log.info("Scheduled %-16s next run %s", job_id, getattr(job, "next_run_time", "?"))

    log.info(
        "Overseer running (tz=%s, deadline %s, reminder %s, heartbeat %02d:00)",
        settings.TIMEZONE,
        judge.DEADLINE.strftime("%H:%M"),
        judge.REMINDER.strftime("%H:%M"),
        settings.HEARTBEAT_HOUR,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("Overseer heartbeat stopped")
