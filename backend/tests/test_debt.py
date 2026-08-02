"""The debt state machine: claim within 24h or it is gone forever.

Streak and money must stay independent — see test_ledger.py for the streak side.
"""

from datetime import datetime, timedelta, timezone

import pytest

from features.enforcement.debt import (
    CLAIM_WINDOW,
    DebtFacts,
    DebtState,
    expires_at,
    is_claimable,
    should_expire,
    state,
)

FAILED = datetime(2026, 7, 27, 20, 0, tzinfo=timezone.utc)  # 14:00 local Monday


def test_no_failure_means_nothing_is_owed():
    assert state(DebtFacts(), FAILED) is DebtState.NONE
    assert is_claimable(DebtFacts(), FAILED) is False


def test_open_immediately_after_failure():
    facts = DebtFacts(failed_at=FAILED)
    assert state(facts, FAILED) is DebtState.OPEN
    assert is_claimable(facts, FAILED) is True


def test_still_open_one_hour_later():
    facts = DebtFacts(failed_at=FAILED)
    assert state(facts, FAILED + timedelta(hours=1)) is DebtState.OPEN


def test_claimed_inside_the_window():
    facts = DebtFacts(failed_at=FAILED, claimed_at=FAILED + timedelta(hours=3))
    assert state(facts, FAILED + timedelta(hours=4)) is DebtState.CLAIMED
    # Already claimed — not claimable again.
    assert is_claimable(facts, FAILED + timedelta(hours=4)) is False


def test_exactly_24h_is_still_claimable():
    """The window is inclusive at its edge."""
    facts = DebtFacts(failed_at=FAILED)
    now = FAILED + CLAIM_WINDOW
    assert state(facts, now) is DebtState.OPEN
    assert is_claimable(facts, now) is True


def test_expires_at_24h_plus_one_second():
    facts = DebtFacts(failed_at=FAILED)
    now = FAILED + CLAIM_WINDOW + timedelta(seconds=1)
    assert state(facts, now) is DebtState.EXPIRED
    assert is_claimable(facts, now) is False


def test_expired_debt_is_never_payable_again():
    facts = DebtFacts(failed_at=FAILED)
    much_later = FAILED + timedelta(days=30)
    assert state(facts, much_later) is DebtState.EXPIRED
    assert is_claimable(facts, much_later) is False


def test_a_claim_recorded_after_the_window_does_not_count():
    """The machine does not trust its callers to have checked the window."""
    facts = DebtFacts(
        failed_at=FAILED,
        claimed_at=FAILED + CLAIM_WINDOW + timedelta(seconds=1),
    )
    assert state(facts, FAILED + timedelta(days=2)) is DebtState.EXPIRED


def test_expires_at_is_exactly_24h():
    assert expires_at(FAILED) == FAILED + timedelta(hours=24)


@pytest.mark.parametrize(
    "facts, now, expected",
    [
        (DebtFacts(), FAILED, False),
        (DebtFacts(failed_at=FAILED), FAILED + timedelta(hours=1), False),
        (DebtFacts(failed_at=FAILED), FAILED + timedelta(hours=25), True),
        (
            DebtFacts(failed_at=FAILED, claimed_at=FAILED + timedelta(hours=1)),
            FAILED + timedelta(hours=25),
            False,
        ),
    ],
)
def test_should_expire(facts, now, expected):
    """Only an unclaimed, past-window debt needs a DEBT_EXPIRED event written."""
    assert should_expire(facts, now) is expected


def test_debt_module_is_pure():
    import features.enforcement.debt as d

    source = open(d.__file__).read()
    for forbidden in ("openai", "twilio", "core.db", "httpx", "SessionLocal"):
        assert forbidden not in source, f"debt.py must not reference {forbidden}"
