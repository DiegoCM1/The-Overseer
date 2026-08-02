"""The heartbeat: poll life-os, escalate anything overdue, exactly once per step.

tick() is async (httpx). The blocking work (DB dedupe + Twilio) runs in a thread
so it never stalls the event loop.
"""

import asyncio
import logging
from datetime import date, datetime

from core.config import settings
from core.db import SessionLocal
from features.monitor import escalation, messages
from features.monitor.lifeos_client import get_misses
from features.monitor.models import Notification
from features.notifications.twilio_client import make_call, send_whatsapp

log = logging.getLogger("overseer")


async def tick() -> None:
    try:
        data = await get_misses()
    except Exception as e:
        log.warning("Overseer tick: could not reach life-os: %s", e)
        return

    # _process runs in a worker thread, so an exception here does NOT surface as a
    # normal traceback — it propagates back through APScheduler's executor. Catch it
    # so one malformed payload can't kill the heartbeat, and log enough to diagnose:
    # the life-os contract is unvalidated, so a shape change lands here as a KeyError.
    try:
        await asyncio.to_thread(_process, data)
    except Exception:
        log.exception(
            "Overseer tick failed while processing life-os payload "
            "(top-level keys=%s, goal count=%s)",
            sorted(data) if isinstance(data, dict) else type(data).__name__,
            len(data.get("goals", [])) if isinstance(data, dict) else "n/a",
        )


def _process(data: dict) -> None:
    now = datetime.fromisoformat(data["now"])
    log_date = date.fromisoformat(data["date"])
    for goal in data["goals"]:
        if goal["severity"] not in escalation.BAD:
            continue
        mins = escalation.minutes_past_deadline(goal["deadline_hour"], now)
        target = escalation.desired_level(goal["severity"], mins)
        # Fire every step up to the desired level that hasn't fired yet, so a
        # first poll that's already "really bad" still leaves the L1/L2 trail.
        for level in range(1, target + 1):
            if _already_sent(log_date, goal["goal_id"], level):
                continue
            _deliver(goal, level, now, log_date)


def _deliver(goal: dict, level: int, now: datetime, log_date: date) -> None:
    text = messages.compose(goal, level)
    try:
        if level >= 3 and settings.ENABLE_CALLS and not escalation.in_quiet_hours(now):
            make_call(text)
            channel = "call"
        elif level >= 3:
            # Calls off or quiet hours → deliver the call-worthy message as WhatsApp.
            send_whatsapp(f"[CALL-WORTHY] {text}")
            channel = "whatsapp"
        else:
            send_whatsapp(text)
            channel = "whatsapp"
    except Exception as e:
        # Don't record on failure → the next poll retries this step.
        log.warning("Overseer deliver failed (%s L%d): %s", goal["goal_id"], level, e)
        return
    _record(log_date, goal["goal_id"], level, channel)
    log.info("Overseer sent %s L%d via %s", goal["goal_id"], level, channel)


def _already_sent(log_date: date, goal_id: str, level: int) -> bool:
    with SessionLocal() as db:
        return (
            db.query(Notification)
            .filter_by(log_date=log_date, goal_id=goal_id, level=level)
            .first()
            is not None
        )


def _record(log_date: date, goal_id: str, level: int, channel: str) -> None:
    with SessionLocal() as db:
        db.add(Notification(log_date=log_date, goal_id=goal_id, level=level, channel=channel))
        try:
            db.commit()
        except Exception:
            # Unique constraint lost a race → someone else already recorded it.
            db.rollback()
