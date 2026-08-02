"""The inbound webhook — the only write path into the ledger.

The signature check is the security boundary: without it this endpoint is an
unauthenticated "mark today as done" button on the public internet. It is tested
with real Twilio-computed signatures, not mocks.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from core.config import settings
from features.enforcement import ledger, router as webhook_router, service, xverify
from features.enforcement.ledger import EventType

MX = ZoneInfo("America/Mexico_City")
MON = date(2026, 7, 27)
URL_PATH = "/webhooks/twilio"
POST_URL = "https://x.com/DiegoCM1/status/1234567890123456789"


def local(day: date, h: int, m: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, h, m, tzinfo=MX).astimezone(timezone.utc)


@pytest.fixture
def client(monkeypatch, db):
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://overseer.test")
    monkeypatch.setattr(settings, "TWILIO_WHATSAPP_TO", "whatsapp:+525512345678")
    monkeypatch.setattr(settings, "TWILIO_WHATSAPP_DANIEL", "whatsapp:+525598765432")

    class _Session:
        def __enter__(self):
            return db

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(webhook_router, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(service, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(webhook_router, "_reply", lambda text: None)
    monkeypatch.setattr(service, "_notify", lambda to, body, who: True)
    monkeypatch.setattr(ledger, "utcnow", lambda: local(MON, 10))

    app = FastAPI()
    app.include_router(webhook_router.router)
    return TestClient(app)


def signed(client, form: dict):
    """POST with a genuine Twilio signature over the public URL."""
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    sig = validator.compute_signature(f"https://overseer.test{URL_PATH}", form)
    return client.post(URL_PATH, data=form, headers={"X-Twilio-Signature": sig})


# --------------------------------------------------------------------------- #
# Signature verification
# --------------------------------------------------------------------------- #


def test_missing_signature_is_rejected(client):
    resp = client.post(URL_PATH, data={"From": "whatsapp:+525512345678", "Body": "hi"})
    assert resp.status_code == 403


def test_bad_signature_is_rejected(client):
    resp = client.post(
        URL_PATH,
        data={"From": "whatsapp:+525512345678", "Body": "hi"},
        headers={"X-Twilio-Signature": "obviously-wrong"},
    )
    assert resp.status_code == 403


def test_forged_post_without_signature_writes_nothing(client, db):
    client.post(URL_PATH, data={"From": "whatsapp:+525512345678", "Body": POST_URL})
    assert ledger.all_events(db) == []


def test_valid_signature_is_accepted(client, monkeypatch):
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    resp = signed(client, {"From": "whatsapp:+525512345678", "Body": "hello"})
    assert resp.status_code == 200


# --------------------------------------------------------------------------- #
# Diego: post submission
# --------------------------------------------------------------------------- #


async def _async_true(url):
    return True


async def _async_false(url):
    return False


def test_valid_post_url_is_logged(client, db, monkeypatch):
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    signed(client, {"From": "whatsapp:+525512345678", "Body": f"done {POST_URL}"})

    event = ledger.get_event(db, MON, EventType.POST_LOGGED)
    assert event is not None
    assert event.payload["url"] == POST_URL


def test_url_that_fails_existence_check_is_not_logged(client, db, monkeypatch):
    monkeypatch.setattr(xverify, "post_exists", _async_false)
    signed(client, {"From": "whatsapp:+525512345678", "Body": POST_URL})

    assert not ledger.has_event(db, MON, EventType.POST_LOGGED)


def test_message_without_a_url_is_ignored(client, db, monkeypatch):
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    signed(client, {"From": "whatsapp:+525512345678", "Body": "I'll do it later I promise"})

    assert not ledger.has_event(db, MON, EventType.POST_LOGGED)


def test_resubmission_does_not_overwrite_the_first_entry(client, db, monkeypatch):
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    signed(client, {"From": "whatsapp:+525512345678", "Body": POST_URL})
    other = "https://x.com/DiegoCM1/status/9999999999999999999"
    signed(client, {"From": "whatsapp:+525512345678", "Body": other})

    event = ledger.get_event(db, MON, EventType.POST_LOGGED)
    assert event.payload["url"] == POST_URL  # the first one stands


def test_unknown_sender_is_ignored(client, db, monkeypatch):
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    signed(client, {"From": "whatsapp:+521111111111", "Body": POST_URL})

    assert ledger.all_events(db) == []


def test_mexican_number_prefix_variants_match(client, db, monkeypatch):
    """+521... and +52... are the same human. A strict compare would drop posts."""
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    signed(client, {"From": "whatsapp:+5215512345678", "Body": POST_URL})

    assert ledger.has_event(db, MON, EventType.POST_LOGGED)


# --------------------------------------------------------------------------- #
# Daniel: debt claim
# --------------------------------------------------------------------------- #


def test_daniel_claims_an_open_debt(client, db):
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=local(MON, 14))
    ledger.utcnow = lambda: local(MON, 15)  # inside the 24h window

    signed(client, {"From": "whatsapp:+525598765432", "Body": "págame"})
    assert ledger.has_event(db, MON, EventType.DEBT_CLAIMED)


def test_claim_without_accent_also_works(client, db):
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=local(MON, 14))
    ledger.utcnow = lambda: local(MON, 15)

    signed(client, {"From": "whatsapp:+525598765432", "Body": "PAGAME"})
    assert ledger.has_event(db, MON, EventType.DEBT_CLAIMED)


def test_claim_with_no_open_debt_writes_nothing(client, db):
    signed(client, {"From": "whatsapp:+525598765432", "Body": "págame"})
    assert not ledger.has_event(db, MON, EventType.DEBT_CLAIMED)


def test_diego_cannot_claim_his_own_debt(client, db, monkeypatch):
    """Diego sending 'págame' must not register a claim — he is not the claimant."""
    monkeypatch.setattr(xverify, "post_exists", _async_true)
    ledger.append(db, EventType.VERDICT_FAIL, MON, occurred_at=local(MON, 14))

    signed(client, {"From": "whatsapp:+525512345678", "Body": "págame"})
    assert not ledger.has_event(db, MON, EventType.DEBT_CLAIMED)


# --------------------------------------------------------------------------- #
# URL extraction
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "text, expected",
    [
        (POST_URL, POST_URL),
        (f"here you go {POST_URL} 🔥", POST_URL),
        ("https://twitter.com/foo/status/123", "https://twitter.com/foo/status/123"),
        ("https://x.com/foo", None),
        ("https://youtube.com/watch?v=1", None),
        ("", None),
    ],
)
def test_extract_post_url(text, expected):
    assert xverify.extract_post_url(text) == expected
