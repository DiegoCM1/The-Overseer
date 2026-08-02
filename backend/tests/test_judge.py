"""The verdict must be deterministic and timezone-correct.

Every case here is written in local (America/Mexico_City) terms and then converted
to the UTC instant the system would actually store, because that conversion is
where a bug would hide. UTC-6 year-round: Mexico abolished DST in 2022.
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from features.enforcement.judge import (
    DEADLINE,
    Evidence,
    Verdict,
    deadline_at,
    is_required,
    local_date,
    verdict,
)

MX = ZoneInfo("America/Mexico_City")

MONDAY = date(2026, 7, 27)
SATURDAY = date(2026, 8, 1)
SUNDAY = date(2026, 8, 2)


def local(day: date, h: int, m: int = 0, s: int = 0) -> datetime:
    """A local instant, stored the way the system stores it: as UTC."""
    return datetime(day.year, day.month, day.day, h, m, s, tzinfo=MX).astimezone(
        timezone.utc
    )


# --------------------------------------------------------------------------- #
# Which days demand anything
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "day, required",
    [
        (MONDAY, True),
        (date(2026, 7, 31), True),   # Friday
        (SATURDAY, False),
        (SUNDAY, False),
    ],
)
def test_is_required(day, required):
    assert is_required(day) is required


def test_weekend_is_not_required_even_with_no_post():
    """Weekends demand nothing. NOT_REQUIRED is a third state, not a PASS."""
    assert verdict(Evidence(None), local(SATURDAY, 23, 59)) is Verdict.NOT_REQUIRED
    assert verdict(Evidence(None), local(SUNDAY, 9)) is Verdict.NOT_REQUIRED


# --------------------------------------------------------------------------- #
# The 14:00 boundary — the whole point of the module
# --------------------------------------------------------------------------- #


def test_post_well_before_deadline_passes():
    assert verdict(Evidence(local(MONDAY, 9, 15)), local(MONDAY, 14)) is Verdict.PASS


def test_post_exactly_at_deadline_passes():
    """14:00:00 is inclusive."""
    assert verdict(Evidence(local(MONDAY, 14, 0, 0)), local(MONDAY, 14)) is Verdict.PASS


def test_post_one_second_late_fails():
    """14:00:01 fails. This is the boundary the whole bet turns on."""
    assert verdict(Evidence(local(MONDAY, 14, 0, 1)), local(MONDAY, 14)) is Verdict.FAIL


def test_no_post_fails():
    """Absence of evidence is a miss — the default state is failure."""
    assert verdict(Evidence(None), local(MONDAY, 14)) is Verdict.FAIL


def test_post_from_a_different_local_day_does_not_satisfy_today():
    """Yesterday's post cannot be re-used to cover today."""
    yesterday = local(MONDAY - timedelta(days=1), 13)
    assert verdict(Evidence(yesterday), local(MONDAY, 14)) is Verdict.FAIL


# --------------------------------------------------------------------------- #
# Timezone correctness — a bug here silently grants free days
# --------------------------------------------------------------------------- #


def test_deadline_is_2pm_local_not_2pm_utc():
    d = deadline_at(MONDAY)
    assert (d.hour, d.minute) == (DEADLINE.hour, DEADLINE.minute)
    assert d.utcoffset() == timedelta(hours=-6)
    # 14:00 local == 20:00 UTC
    assert d.astimezone(timezone.utc).hour == 20


def test_utc_instant_just_before_2pm_local_passes():
    """19:59:59Z is 13:59:59 local — a pass, even though UTC already reads 19:xx."""
    submitted = datetime(2026, 7, 27, 19, 59, 59, tzinfo=timezone.utc)
    assert verdict(Evidence(submitted), local(MONDAY, 14)) is Verdict.PASS


def test_utc_instant_just_after_2pm_local_fails():
    submitted = datetime(2026, 7, 27, 20, 0, 1, tzinfo=timezone.utc)
    assert verdict(Evidence(submitted), local(MONDAY, 14)) is Verdict.FAIL


def test_late_evening_utc_rolls_to_the_next_local_day():
    """23:00 local Monday is 05:00Z Tuesday. local_date must say Monday."""
    assert local_date(local(MONDAY, 23)) == MONDAY


def test_naive_datetime_is_rejected_not_assumed():
    with pytest.raises(ValueError, match="timezone-aware"):
        verdict(Evidence(None), datetime(2026, 7, 27, 14, 0))


def test_no_llm_or_io_imported_in_the_verdict_path():
    """The judge must stay pure. If this fails, someone gave the judge a phone."""
    import features.enforcement.judge as j

    source = open(j.__file__).read()
    for forbidden in ("openai", "twilio", "core.db", "httpx", "requests", "SessionLocal"):
        assert forbidden not in source, f"judge.py must not reference {forbidden}"
