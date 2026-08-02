"""Orchestration: the only place where the pure domain meets the outside world.

judge.py and debt.py decide. ledger.py remembers. This module is the plumbing that
connects them to APScheduler, Twilio and healthchecks.io — and it is deliberately
thin, because every line here is a line that could get a decision wrong.

Concurrency follows the pattern already proven in features/monitor/service.py: the
scheduler entrypoints are async, and all blocking work (sync SQLAlchemy + Twilio's
sync HTTP client) is pushed onto a worker thread with asyncio.to_thread so it never
stalls the event loop.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta

from core.config import settings
from core.db import SessionLocal
from features.enforcement import debt, healthcheck, judge, ledger, messages
from features.enforcement.debt import DebtFacts
from features.enforcement.judge import Evidence, Verdict
from features.enforcement.ledger import EventType
from features.notifications.twilio_client import send_whatsapp

log = logging.getLogger("overseer")

# How far back the debt sweep looks. Debts live 24h, so this is generous.
_SWEEP_DAYS = 30


def _notify(to: str | None, body: str, who: str) -> bool:
    """Send one WhatsApp. Returns False on failure instead of raising — a delivery
    problem must never prevent the verdict from being recorded."""
    if not to:
        log.error("No WhatsApp number configured for %s; message dropped: %s", who, body)
        return False
    try:
        send_whatsapp(body, to=to)
        log.info("Notified %s", who)
        return True
    except Exception as e:
        log.error("Failed to notify %s: %s", who, e)
        return False


# --------------------------------------------------------------------------- #
# 13:30 local, weekdays — 30 minutes' warning
# --------------------------------------------------------------------------- #


async def run_reminder() -> None:
    await asyncio.to_thread(_reminder)


def _reminder() -> None:
    now = ledger.utcnow()
    day = judge.local_date(now)

    if not judge.is_required(day):
        return

    with SessionLocal() as db:
        if ledger.has_event(db, day, EventType.POST_LOGGED):
            log.info("Reminder skipped: post already logged for %s", day)
            return

        minutes_left = int(
            (judge.deadline_at(day) - judge.to_local(now)).total_seconds() // 60
        )
        body = messages.compose_reminder(max(minutes_left, 0))

        if _notify(settings.TWILIO_WHATSAPP_TO, body, "Diego (reminder)"):
            # Recorded only after a successful send, so a failed send retries
            # conceptually on the next run rather than being marked done.
            ledger.append(db, EventType.REMINDER_SENT, day, {"minutes_left": minutes_left})


# --------------------------------------------------------------------------- #
# 14:00 local, weekdays — the judgment
# --------------------------------------------------------------------------- #


async def run_judgment() -> None:
    try:
        await asyncio.to_thread(_judgment)
    finally:
        # Ping even if judgment raised: healthchecks tracks that the process is
        # alive and running its schedule. A silent skip is the failure we fear.
        await healthcheck.ping()


def _judgment() -> None:
    now = ledger.utcnow()
    day = judge.local_date(now)

    with SessionLocal() as db:
        _sweep_expired_debts(db, now)

        if not judge.is_required(day):
            log.info("No obligation on %s (%s)", day, day.strftime("%A"))
            return

        post = ledger.get_event(db, day, EventType.POST_LOGGED)
        evidence = Evidence(post_logged_at=_as_utc(post.occurred_at) if post else None)

        result = judge.verdict(evidence, now)
        log.info("Verdict for %s: %s", day, result)

        if result is Verdict.NOT_REQUIRED:
            return

        event_type = (
            EventType.VERDICT_PASS if result is Verdict.PASS else EventType.VERDICT_FAIL
        )

        # Streak as it stood BEFORE this verdict landed, for the message copy.
        streak_before = ledger.current_streak(db, day - timedelta(days=1))

        written = ledger.append(db, event_type, day, {"verdict": str(result)})
        if written is None:
            # A previous tick already judged today. Do not notify twice.
            log.info("Verdict for %s already recorded; skipping notifications", day)
            return

        if result is Verdict.FAIL:
            _notify(
                settings.TWILIO_WHATSAPP_TO,
                messages.compose_fail_for_diego(streak_before),
                "Diego (verdict FAIL)",
            )
            _notify(
                settings.TWILIO_WHATSAPP_DANIEL,
                messages.compose_fail_for_daniel(streak_before),
                "Daniel (verdict FAIL)",
            )


def _as_utc(dt: datetime) -> datetime:
    """sqlite hands back naive datetimes; Postgres returns aware ones. The judge
    rejects naive input by design, so normalise here at the storage boundary."""
    from datetime import timezone

    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Debt sweep — expire anything unclaimed past its 24h window
# --------------------------------------------------------------------------- #


def _sweep_expired_debts(db, now: datetime) -> None:
    """Write DEBT_EXPIRED for failures whose claim window has closed.

    Idempotent: the ledger's unique constraint rejects a second DEBT_EXPIRED for
    the same day, so running this on every judgment is free.
    """
    horizon = judge.local_date(now) - timedelta(days=_SWEEP_DAYS)

    for event in ledger.all_events(db):
        if event.event_type != str(EventType.VERDICT_FAIL) or event.log_date < horizon:
            continue

        day = event.log_date
        if ledger.has_event(db, day, EventType.DEBT_EXPIRED):
            continue

        claimed = ledger.get_event(db, day, EventType.DEBT_CLAIMED)
        facts = DebtFacts(
            failed_at=_as_utc(event.occurred_at),
            claimed_at=_as_utc(claimed.occurred_at) if claimed else None,
        )

        if debt.should_expire(facts, now):
            ledger.append(db, EventType.DEBT_EXPIRED, day, {"amount_mxn": debt.DEBT_AMOUNT_MXN})
            log.info("Debt for %s expired unclaimed", day)


def open_debt_day(db, now: datetime) -> date | None:
    """The most recent day with a claimable debt, or None.

    Used by the inbound webhook when Daniel replies 'págame'.
    """
    for event in sorted(ledger.all_events(db), key=lambda e: e.log_date, reverse=True):
        if event.event_type != str(EventType.VERDICT_FAIL):
            continue
        day = event.log_date
        claimed = ledger.get_event(db, day, EventType.DEBT_CLAIMED)
        facts = DebtFacts(
            failed_at=_as_utc(event.occurred_at),
            claimed_at=_as_utc(claimed.occurred_at) if claimed else None,
        )
        if debt.is_claimable(facts, now):
            return day
    return None


# --------------------------------------------------------------------------- #
# Daily — the heartbeat to Daniel
# --------------------------------------------------------------------------- #


async def run_heartbeat() -> None:
    await asyncio.to_thread(_heartbeat)


def _heartbeat() -> None:
    """Send Daniel the current streak.

    This is not a nicety. It makes Daniel's WhatsApp thread an append-only replica
    of the history, held outside any system Diego controls. Rewriting the ledger
    would still leave a contradicting record on someone else's phone.
    """
    now = ledger.utcnow()
    day = judge.local_date(now)

    with SessionLocal() as db:
        streak = ledger.current_streak(db, day)
        body = messages.compose_heartbeat(streak)

        if _notify(settings.TWILIO_WHATSAPP_DANIEL, body, "Daniel (heartbeat)"):
            ledger.append(db, EventType.HEARTBEAT_SENT, day, {"streak": streak})
