"""Pure escalation policy — no I/O. Deterministic so accountability stays reliable."""

from datetime import datetime

from core.config import settings

# Severities from life-os that warrant escalation. "late" is minor; we don't nag.
BAD = {"missed", "failed"}


def minutes_past_deadline(deadline_hour: int | None, now: datetime) -> float:
    """Minutes since the goal's deadline today, using life-os's authoritative `now`."""
    if deadline_hour is None:
        return 0.0
    deadline = now.replace(hour=deadline_hour, minute=0, second=0, microsecond=0)
    return max(0.0, (now - deadline).total_seconds() / 60.0)


def desired_level(severity: str, minutes_past: float) -> int:
    """0 = nothing; 1 = nudge; 2 = firmer; 3 = call-worthy."""
    if severity not in BAD:
        return 0
    if severity == "failed" or minutes_past >= settings.GRACE2_MIN:
        return 3
    if minutes_past >= settings.GRACE1_MIN:
        return 2
    return 1


def in_quiet_hours(now: datetime) -> bool:
    """True inside [QUIET_START, QUIET_END); handles the window wrapping midnight."""
    h = now.hour
    start, end = settings.QUIET_START, settings.QUIET_END
    if start <= end:
        return start <= h < end
    return h >= start or h < end
