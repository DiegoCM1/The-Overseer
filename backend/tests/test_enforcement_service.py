"""The orchestration layer: judgment, debt sweep, heartbeat.

Twilio and the LLM are monkeypatched out. Nothing here touches the network.
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from features.enforcement import ledger, service
from features.enforcement.ledger import EventType

MX = ZoneInfo("America/Mexico_City")
MON = date(2026, 7, 27)
SAT = date(2026, 8, 1)


def local(day: date, h: int, m: int = 0, s: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, h, m, s, tzinfo=MX).astimezone(
        timezone.utc
    )


@pytest.fixture
def sent(monkeypatch, db):
    """Capture notifications; pin SessionLocal and the clock to the test db."""
    outbox = []
    monkeypatch.setattr(
        service, "_notify", lambda to, body, who: outbox.append((who, body)) or True
    )

    class _Session:
        def __enter__(self):
            return db

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(service, "SessionLocal", lambda: _Session())
    # Deterministic copy — no LLM calls in tests.
    monkeypatch.setattr(service.messages, "compose_fail_for_diego", lambda s: f"FAIL/diego/{s}")
    monkeypatch.setattr(service.messages, "compose_fail_for_daniel", lambda s: f"FAIL/daniel/{s}")
    monkeypatch.setattr(service.messages, "compose_reminder", lambda m: f"REMIND/{m}")
    monkeypatch.setattr(service.messages, "compose_heartbeat", lambda s: f"BEAT/{s}")
    return outbox


def at(monkeypatch, when: datetime):
    monkeypatch.setattr(service.ledger, "utcnow", lambda: when)


# --------------------------------------------------------------------------- #
# Judgment
# --------------------------------------------------------------------------- #


def test_no_post_by_2pm_writes_fail_and_notifies_both(monkeypatch, db, sent):
    at(monkeypatch, local(MON, 14, 0, 0))
    service._judgment()

    assert ledger.has_event(db, MON, EventType.VERDICT_FAIL)
    who = [w for w, _ in sent]
    assert any("Diego" in w for w in who)
    assert any("Daniel" in w for w in who)


def test_on_time_post_writes_pass_and_notifies_nobody(monkeypatch, db, sent):
    ledger.append(db, EventType.POST_LOGGED, MON, occurred_at=local(MON, 9))
    at(monkeypatch, local(MON, 14, 0, 0))
    service._judgment()

    assert ledger.has_event(db, MON, EventType.VERDICT_PASS)
    assert sent == []


def test_post_one_second_late_is_a_fail(monkeypatch, db, sent):
    ledger.append(db, EventType.POST_LOGGED, MON, occurred_at=local(MON, 14, 0, 1))
    at(monkeypatch, local(MON, 14, 0, 5))
    service._judgment()

    assert ledger.has_event(db, MON, EventType.VERDICT_FAIL)


def test_double_tick_writes_one_verdict_and_notifies_once(monkeypatch, db, sent):
    at(monkeypatch, local(MON, 14))
    service._judgment()
    first = len(sent)
    service._judgment()

    events = [e for e in ledger.all_events(db) if e.event_type.startswith("VERDICT")]
    assert len(events) == 1
    assert len(sent) == first  # no duplicate notifications


def test_weekend_produces_no_verdict(monkeypatch, db, sent):
    at(monkeypatch, local(SAT, 14))
    service._judgment()

    assert [e for e in ledger.all_events(db) if e.event_type.startswith("VERDICT")] == []
    assert sent == []


# --------------------------------------------------------------------------- #
# Reminder
# --------------------------------------------------------------------------- #


def test_reminder_fires_when_nothing_logged(monkeypatch, db, sent):
    at(monkeypatch, local(MON, 13, 30))
    service._reminder()

    assert ledger.has_event(db, MON, EventType.REMINDER_SENT)
    assert sent and "REMIND/30" in sent[0][1]


def test_reminder_skipped_when_post_already_logged(monkeypatch, db, sent):
    ledger.append(db, EventType.POST_LOGGED, MON, occurred_at=local(MON, 10))
    at(monkeypatch, local(MON, 13, 30))
    service._reminder()

    assert not ledger.has_event(db, MON, EventType.REMINDER_SENT)
    assert sent == []


# --------------------------------------------------------------------------- #
# Debt sweep
# --------------------------------------------------------------------------- #


def test_unclaimed_debt_expires_after_24h(monkeypatch, db, sent):
    failed = local(MON, 14)
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=failed)

    service._sweep_expired_debts(db, failed + timedelta(hours=24))
    assert not ledger.has_event(db, MON, EventType.DEBT_EXPIRED)  # inclusive edge

    service._sweep_expired_debts(db, failed + timedelta(hours=24, seconds=1))
    assert ledger.has_event(db, MON, EventType.DEBT_EXPIRED)


def test_claimed_debt_never_expires(monkeypatch, db, sent):
    failed = local(MON, 14)
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=failed)
    ledger.append(
        db, EventType.DEBT_CLAIMED, MON, occurred_at=failed + timedelta(hours=2)
    )

    service._sweep_expired_debts(db, failed + timedelta(days=5))
    assert not ledger.has_event(db, MON, EventType.DEBT_EXPIRED)


def test_open_debt_day_finds_claimable_debt(db):
    failed = local(MON, 14)
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=failed)

    assert service.open_debt_day(db, failed + timedelta(hours=1)) == MON
    assert service.open_debt_day(db, failed + timedelta(hours=25)) is None


def test_streak_is_unaffected_by_debt_outcome(db):
    """Money and streak are independent — the whole point of the separation."""
    failed = local(MON, 14)
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=failed)
    before = ledger.current_streak(db, MON)

    ledger.append(db, EventType.DEBT_CLAIMED, MON, occurred_at=failed + timedelta(hours=1))
    assert ledger.current_streak(db, MON) == before


# --------------------------------------------------------------------------- #
# Heartbeat
# --------------------------------------------------------------------------- #


def test_heartbeat_reports_the_derived_streak(monkeypatch, db, sent):
    ledger.append(db, EventType.VERDICT_PASS, MON, occurred_at=local(MON, 14))
    at(monkeypatch, local(MON, 20))
    service._heartbeat()

    assert ledger.has_event(db, MON, EventType.HEARTBEAT_SENT)
    assert sent and sent[0][1] == "BEAT/1"
