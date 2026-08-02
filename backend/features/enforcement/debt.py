"""The debt state machine. Pure — no I/O, no database, no Twilio.

A VERDICT_FAIL opens a debt of 200 MXN. Daniel has 24 hours from the moment of
failure to claim it by replying. Unclaimed past that window it becomes
DEBT_EXPIRED and is never payable again.

**Streak and money are fully independent.** The streak resets on VERDICT_FAIL
whether or not the debt is ever claimed, and nothing in this module touches the
streak. They are deliberately not coupled: coupling them would create an
incentive to argue about the debt in order to move the streak, which is exactly
the kind of negotiation the design is built to prevent.

Boundary: the window is inclusive. At exactly 24h the debt is still claimable;
at 24h + 1s it is expired.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

CLAIM_WINDOW = timedelta(hours=24)
DEBT_AMOUNT_MXN = 200


class DebtState(StrEnum):
    NONE = "NONE"        # no failure that day, so nothing is owed
    OPEN = "OPEN"        # failed, inside the window, unclaimed — claimable now
    CLAIMED = "CLAIMED"  # Daniel claimed it in time
    EXPIRED = "EXPIRED"  # window closed unclaimed; never payable


@dataclass(frozen=True)
class DebtFacts:
    """Everything the state machine is allowed to look at, all UTC instants."""

    failed_at: datetime | None = None
    claimed_at: datetime | None = None


def expires_at(failed_at: datetime) -> datetime:
    return failed_at + CLAIM_WINDOW


def state(facts: DebtFacts, now: datetime) -> DebtState:
    if facts.failed_at is None:
        return DebtState.NONE

    deadline = expires_at(facts.failed_at)

    if facts.claimed_at is not None:
        # A claim recorded after the window is not a valid claim. This should be
        # unreachable if claims go through is_claimable(), but the state machine
        # must not depend on its callers being correct.
        return DebtState.CLAIMED if facts.claimed_at <= deadline else DebtState.EXPIRED

    return DebtState.EXPIRED if now > deadline else DebtState.OPEN


def is_claimable(facts: DebtFacts, now: datetime) -> bool:
    """Can Daniel claim right now? Only an OPEN debt can be claimed."""
    return state(facts, now) is DebtState.OPEN


def should_expire(facts: DebtFacts, now: datetime) -> bool:
    """True when an unclaimed debt has passed its window and needs a DEBT_EXPIRED
    event written. Idempotency of that write is the ledger's job, not ours."""
    return state(facts, now) is DebtState.EXPIRED and facts.claimed_at is None
