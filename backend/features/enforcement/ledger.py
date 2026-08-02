"""The append-only event log, and the streak fold over it.

This module is the system's memory. Everything else derives from it.

Two invariants, and neither is negotiable:

1. **Append only.** There is no update path and no delete path in this module.
   That is enforced in the database too (see the migration that installs
   ``events_no_mutate``), because a convention the author can ignore is not a
   control — and here the author is the adversary.

2. **The streak is never stored.** It is folded from the log on every read. There
   is no streak column, no cached counter, and no function anywhere that writes a
   streak value. To fake a streak you would have to forge dated verdict events,
   which is a deliberate, visible act rather than a one-character edit.

Timezones: ``occurred_at`` is an absolute UTC instant. ``log_date`` is the *local*
(America/Mexico_City) calendar date the event belongs to, and it is supplied by the
caller — this module deliberately owns no clock, so there is exactly one place
(``judge.py``) where UTC becomes a local date.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Iterable, Sequence

from sqlalchemy import JSON, Column, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.db import Base


class EventType(StrEnum):
    POST_LOGGED = "POST_LOGGED"
    VERDICT_PASS = "VERDICT_PASS"
    VERDICT_FAIL = "VERDICT_FAIL"
    DEBT_CLAIMED = "DEBT_CLAIMED"
    DEBT_EXPIRED = "DEBT_EXPIRED"
    HEARTBEAT_SENT = "HEARTBEAT_SENT"
    REMINDER_SENT = "REMINDER_SENT"


# Saturday=5, Sunday=6 per date.weekday(). Weekends demand no post but still
# advance the streak, per the contract.
WEEKEND = {5, 6}

# JSONB on Postgres (indexable, binary); plain JSON on sqlite so tests still run.
_JSON = JSON().with_variant(JSONB(), "postgresql")


class Event(Base):
    """One immutable fact. Never updated, never deleted."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)  # absolute, UTC
    # index=True produces `ix_events_log_date`, matching the migration. The streak
    # fold scans by day, so keep it indexed as the log grows.
    log_date = Column(Date, nullable=False, index=True)            # local calendar date
    payload = Column(_JSON, nullable=False, default=dict)

    __table_args__ = (
        # One event of each type per local day. This is what makes a double
        # scheduler tick harmless: the second verdict/debt/heartbeat is rejected
        # by the database, not by a race-prone "did we already do this?" check.
        UniqueConstraint("log_date", "event_type", name="uq_event_day_type"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Event {self.log_date} {self.event_type}>"


def utcnow() -> datetime:
    """Timezone-aware UTC now. Never use datetime.utcnow() — it returns naive."""
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Writes (append only)
# --------------------------------------------------------------------------- #


def append(
    db: Session,
    event_type: EventType,
    log_date: date,
    payload: dict | None = None,
    occurred_at: datetime | None = None,
) -> Event | None:
    """Append one event. Returns None if this (log_date, event_type) already exists.

    Idempotent by construction: the uniqueness decision belongs to the database,
    so two concurrent ticks cannot both win. Callers treat None as "already done"
    — it is not an error.
    """
    event = Event(
        event_type=str(event_type),
        occurred_at=occurred_at or utcnow(),
        log_date=log_date,
        payload=payload or {},
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        # Lost the race against another tick, or a genuine duplicate. Either way
        # the fact is already recorded, so there is nothing to repair.
        db.rollback()
        return None
    db.refresh(event)
    return event


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #


def has_event(db: Session, log_date: date, event_type: EventType) -> bool:
    return (
        db.query(Event)
        .filter_by(log_date=log_date, event_type=str(event_type))
        .first()
        is not None
    )


def get_event(db: Session, log_date: date, event_type: EventType) -> Event | None:
    return (
        db.query(Event).filter_by(log_date=log_date, event_type=str(event_type)).first()
    )


def all_events(db: Session) -> list[Event]:
    """Whole log, oldest first. The log is one row per event per day — small."""
    return db.query(Event).order_by(Event.log_date, Event.id).all()


# --------------------------------------------------------------------------- #
# The fold — pure, so it is testable without a database
# --------------------------------------------------------------------------- #


def fold_streak(events: Iterable[tuple[date, str]], today: date) -> int:
    """Derive the current streak from ``(log_date, event_type)`` pairs.

    Walks backwards from ``today`` over consecutive calendar days:

    - weekend                  -> counts, nothing was required
    - VERDICT_PASS             -> counts
    - VERDICT_FAIL             -> streak ends here
    - weekday, no verdict yet:
        * if it is ``today``   -> skipped; the 2 PM judgment has not run yet, so
                                  the day is neither earned nor lost
        * otherwise            -> streak ends. **Absence of evidence is a miss** —
                                  a gap must never read as a pass.

    The walk stops at the earliest day the log knows about, so days before the
    system existed are not silently credited as weekends.
    """
    by_day: dict[date, set[str]] = {}
    for log_date, event_type in events:
        by_day.setdefault(log_date, set()).add(event_type)

    if not by_day:
        return 0

    earliest = min(by_day)
    streak = 0
    day = today

    while day >= earliest:
        types = by_day.get(day, set())

        if str(EventType.VERDICT_FAIL) in types:
            break

        if str(EventType.VERDICT_PASS) in types or day.weekday() in WEEKEND:
            streak += 1
        elif day == today:
            # Not yet judged. Neither earned nor lost — look further back.
            pass
        else:
            # A past weekday with no verdict at all. Default state is failure.
            break

        day -= timedelta(days=1)

    return streak


def current_streak(db: Session, today: date) -> int:
    """Load the log and fold it. There is no stored value to read instead."""
    rows: Sequence[tuple[date, str]] = db.query(Event.log_date, Event.event_type).all()
    return fold_streak(rows, today)
