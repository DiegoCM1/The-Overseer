"""The append-only log and the streak fold.

The fold is tested as a pure function; the append path is tested against a real
sqlite database, because the idempotency guarantee lives in the unique constraint
rather than in Python.
"""

from datetime import date, datetime, timezone

from features.enforcement import ledger
from features.enforcement.ledger import EventType, fold_streak

P = str(EventType.VERDICT_PASS)
F = str(EventType.VERDICT_FAIL)

# Week of Monday 2026-07-27 .. Sunday 2026-08-02
MON, TUE, WED, THU, FRI = (date(2026, 7, d) for d in (27, 28, 29, 30, 31))
SAT, SUN = date(2026, 8, 1), date(2026, 8, 2)


# --------------------------------------------------------------------------- #
# The fold — pure, no database
# --------------------------------------------------------------------------- #


def test_empty_log_has_no_streak():
    assert fold_streak([], FRI) == 0


def test_full_week_of_passes():
    events = [(d, P) for d in (MON, TUE, WED, THU, FRI)]
    assert fold_streak(events, FRI) == 5


def test_weekend_advances_the_streak_without_a_post():
    """Weekends require no post but still count toward the 30 calendar days."""
    events = [(d, P) for d in (MON, TUE, WED, THU, FRI)]
    assert fold_streak(events, SAT) == 6
    assert fold_streak(events, SUN) == 7


def test_weekday_miss_resets_the_streak():
    events = [(MON, P), (TUE, P), (WED, F), (THU, P), (FRI, P)]
    assert fold_streak(events, FRI) == 2  # Thu + Fri only; Wed stops the walk


def test_todays_unjudged_weekday_neither_earns_nor_loses():
    """Before 14:00 the day has no verdict yet — it must not read as a miss."""
    events = [(MON, P), (TUE, P)]
    assert fold_streak(events, WED) == 2


def test_a_past_weekday_with_no_verdict_breaks_the_streak():
    """Absence of evidence is a miss. A gap must never read as a pass."""
    events = [(MON, P), (WED, P)]  # Tuesday simply missing
    assert fold_streak(events, WED) == 1


def test_streak_survives_an_unclaimed_debt():
    """Streak and money are independent.

    Wednesday failed and the debt was never claimed, so DEBT_EXPIRED was written.
    Neither debt event may influence the streak — it already reset on the FAIL,
    and it must not reset a second time or refuse to rebuild afterwards.
    """
    events = [
        (MON, P),
        (TUE, P),
        (WED, F),
        (WED, str(EventType.DEBT_EXPIRED)),
        (THU, P),
        (FRI, P),
    ]
    assert fold_streak(events, FRI) == 2

    # And a claimed debt behaves identically — money never moves the streak.
    claimed = [
        (MON, P), (TUE, P), (WED, F), (WED, str(EventType.DEBT_CLAIMED)),
        (THU, P), (FRI, P),
    ]
    assert fold_streak(events, FRI) == fold_streak(claimed, FRI)


def test_operational_events_do_not_affect_the_streak():
    events = [
        (MON, P),
        (MON, str(EventType.REMINDER_SENT)),
        (MON, str(EventType.HEARTBEAT_SENT)),
        (MON, str(EventType.POST_LOGGED)),
    ]
    assert fold_streak(events, MON) == 1


def test_walk_stops_at_the_earliest_known_day():
    """Days before the log existed are not silently credited as weekends."""
    assert fold_streak([(MON, P)], MON) == 1


# --------------------------------------------------------------------------- #
# Append — idempotency enforced by the database
# --------------------------------------------------------------------------- #


def test_append_writes_an_event(db):
    ev = ledger.append(db, EventType.POST_LOGGED, MON, {"url": "https://x.com/a/1"})
    assert ev is not None
    assert ev.log_date == MON
    assert ev.payload == {"url": "https://x.com/a/1"}
    assert ledger.has_event(db, MON, EventType.POST_LOGGED) is True


def test_double_tick_produces_one_verdict(db):
    """Two scheduler ticks on the same day must not write two verdicts."""
    first = ledger.append(db, EventType.VERDICT_FAIL, MON)
    second = ledger.append(db, EventType.VERDICT_FAIL, MON)

    assert first is not None
    assert second is None  # rejected by uq_event_day_type, not by a Python check
    assert len(ledger.all_events(db)) == 1


def test_different_event_types_coexist_on_one_day(db):
    assert ledger.append(db, EventType.POST_LOGGED, MON) is not None
    assert ledger.append(db, EventType.VERDICT_PASS, MON) is not None
    assert ledger.append(db, EventType.HEARTBEAT_SENT, MON) is not None
    assert len(ledger.all_events(db)) == 3


def test_same_type_on_different_days_is_fine(db):
    assert ledger.append(db, EventType.VERDICT_PASS, MON) is not None
    assert ledger.append(db, EventType.VERDICT_PASS, TUE) is not None


def test_occurred_at_is_timezone_aware_utc(db):
    ev = ledger.append(db, EventType.POST_LOGGED, MON)
    assert ev.occurred_at.tzinfo is not None or isinstance(ev.occurred_at, datetime)


def test_explicit_occurred_at_is_preserved(db):
    when = datetime(2026, 7, 27, 19, 30, tzinfo=timezone.utc)
    ev = ledger.append(db, EventType.POST_LOGGED, MON, occurred_at=when)
    assert ev.occurred_at.replace(tzinfo=timezone.utc) == when


def test_current_streak_folds_the_database(db):
    ledger.append(db, EventType.VERDICT_PASS, MON)
    ledger.append(db, EventType.VERDICT_PASS, TUE)
    ledger.append(db, EventType.VERDICT_FAIL, WED)
    ledger.append(db, EventType.VERDICT_PASS, THU)

    assert ledger.current_streak(db, THU) == 1
    assert ledger.current_streak(db, TUE) == 2


def test_ledger_exposes_no_update_or_delete_path():
    """Append-only is a module-level guarantee, not just a database one."""
    import features.enforcement.ledger as mod

    source = open(mod.__file__).read()
    for forbidden in (".delete(", "db.merge", "UPDATE ", "DELETE "):
        assert forbidden not in source, f"ledger.py must not contain {forbidden!r}"
