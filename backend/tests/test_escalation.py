"""The deterministic escalation policy — the reliability-critical core."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from features.monitor import escalation

TZ = ZoneInfo("America/Mexico_City")


def _at(hour):
    return datetime(2026, 7, 1, hour, 0, tzinfo=TZ)


@pytest.mark.parametrize(
    "severity, minutes_past, expected",
    [
        ("ok", 999, 0),        # healthy → nothing
        ("late", 999, 0),      # late is minor → nothing
        ("pending", 999, 0),
        ("missed", 0, 1),      # just missed → nudge
        ("missed", 59, 1),     # still within grace1
        ("missed", 60, 2),     # grace1 → firmer
        ("missed", 180, 3),    # grace2 → call-worthy
        ("failed", 0, 3),      # a "done but too late" failure is call-worthy at once
    ],
)
def test_desired_level(severity, minutes_past, expected):
    assert escalation.desired_level(severity, minutes_past) == expected


def test_minutes_past_deadline():
    assert escalation.minutes_past_deadline(19, _at(20)) == 60.0
    assert escalation.minutes_past_deadline(19, _at(19)) == 0.0
    assert escalation.minutes_past_deadline(None, _at(20)) == 0.0  # no deadline


@pytest.mark.parametrize(
    "hour, expected",
    [(23, True), (3, True), (22, True), (8, False), (12, False), (21, False)],
)
def test_in_quiet_hours(hour, expected):
    # Default window 22:00–08:00 wraps midnight.
    assert escalation.in_quiet_hours(_at(hour)) is expected
