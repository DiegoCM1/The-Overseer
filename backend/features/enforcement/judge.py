"""The verdict function. Pure, deterministic, and the only thing that decides.

Imports nothing from the database, Twilio, or the network — the whole module is
`(evidence, now) -> Verdict`. That is deliberate: a verdict you can reproduce
from two values is a verdict nobody can argue with. **No LLM ever runs here.**

The contract, which lives in code rather than in `.env` on purpose — changing it
should require an edit, a commit and a diff, not a quiet line change in an
untracked file:

- Obligation: one post per weekday (Mon-Fri)
- Deadline: 14:00 America/Mexico_City, inclusive. 14:00:00 passes, 14:00:01 fails.
- Weekends are NOT_REQUIRED — a third state. They demand nothing, and they still
  advance the streak.

Timezones are the sharp edge here. Every instant in the system is stored UTC and
every comparison happens in local time, because a UTC-vs-local mistake around
14:00 silently grants a free day. Naive datetimes are rejected rather than
assumed — an assumption is exactly how that bug gets in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo

from core.config import settings

# Contractual constants. Not configuration.
DEADLINE = time(14, 0)          # 2:00 PM local, inclusive
REMINDER = time(13, 30)         # 30 minutes' warning
WEEKEND = {5, 6}                # date.weekday(): Saturday=5, Sunday=6


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_REQUIRED = "NOT_REQUIRED"


@dataclass(frozen=True)
class Evidence:
    """Everything the judge is allowed to look at.

    A deliberately tiny surface. If it is not in here, it cannot influence the
    verdict — which is what stops "context" from creeping into the decision.
    """

    post_logged_at: datetime | None  # absolute UTC instant, or None if nothing was submitted


def tz() -> ZoneInfo:
    return ZoneInfo(settings.TIMEZONE)


def _require_aware(dt: datetime, name: str) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(
            f"{name} must be timezone-aware; got a naive datetime. "
            "Naive datetimes around the 14:00 boundary silently grant free days."
        )
    return dt


def to_local(dt: datetime) -> datetime:
    """Convert any aware instant into America/Mexico_City."""
    return _require_aware(dt, "datetime").astimezone(tz())


def local_date(dt: datetime) -> date:
    """The local calendar date an instant belongs to. This is the `log_date` key."""
    return to_local(dt).date()


def is_required(day: date) -> bool:
    """True on Mon-Fri. Weekends demand nothing."""
    return day.weekday() not in WEEKEND


def deadline_at(day: date) -> datetime:
    """The exact local instant the obligation is due for a given local date."""
    return datetime.combine(day, DEADLINE, tzinfo=tz())


def reminder_at(day: date) -> datetime:
    return datetime.combine(day, REMINDER, tzinfo=tz())


def verdict(evidence: Evidence, now: datetime) -> Verdict:
    """The whole decision.

    NOT_REQUIRED on weekends. Otherwise PASS only if a post was submitted at or
    before 14:00 local **on the same local day**. Everything else is FAIL —
    absence of evidence is a miss, and so is a post that belongs to another day.
    """
    day = local_date(now)

    if not is_required(day):
        return Verdict.NOT_REQUIRED

    if evidence.post_logged_at is None:
        return Verdict.FAIL

    submitted = to_local(evidence.post_logged_at)

    # A post carried over from another local date does not satisfy today.
    if submitted.date() != day:
        return Verdict.FAIL

    return Verdict.PASS if submitted <= deadline_at(day) else Verdict.FAIL
