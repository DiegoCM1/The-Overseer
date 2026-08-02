"""The one inbound endpoint. This is the ONLY way a fact enters the system.

Everything else in the service is a scheduled read of the ledger. There is no
admin route, no manual verdict override, no streak setter — by design. If you are
about to add a second write endpoint, re-read the design principle first.

Two accepted messages:

- Diego sends an x.com/twitter.com post URL  -> POST_LOGGED (after an existence check)
- Daniel replies 'págame' / 'pagame'         -> DEBT_CLAIMED (only if one is open)

Anything else is logged and ignored.

Every request must carry a valid X-Twilio-Signature. Without that check this
endpoint is an unauthenticated "mark today as done" button on the public internet.
"""

import asyncio
import logging
import re

from fastapi import APIRouter, HTTPException, Request, Response
from twilio.request_validator import RequestValidator

from core.config import settings
from core.db import SessionLocal
from features.enforcement import judge, ledger, messages, service, xverify
from features.enforcement.ledger import EventType
from features.notifications.twilio_client import send_whatsapp

log = logging.getLogger("overseer")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

CLAIM_PATTERN = re.compile(r"\bp[áa]game\b", re.IGNORECASE)

# Empty TwiML: accepted, no auto-reply. Twilio treats a non-2xx as a failure and
# retries, so we always return 200 once the signature is valid.
_EMPTY_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


def _digits(number: str) -> str:
    return re.sub(r"\D", "", number or "")


def _same_number(a: str, b: str) -> bool:
    """Compare on the last 10 digits.

    Mexican numbers arrive as +52... or +521... depending on the channel, so a
    string comparison would silently classify Diego as 'unknown' and drop his
    submissions. Ten digits is the national significant number.
    """
    da, db_ = _digits(a), _digits(b)
    if not da or not db_:
        return False
    return da[-10:] == db_[-10:]


async def _verify_signature(request: Request, form: dict) -> None:
    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status_code=403, detail="missing signature")

    # Build the URL from PUBLIC_BASE_URL rather than request.url: behind Railway's
    # proxy the app sees http://internal-host, but Twilio signed the public https
    # URL, and the signature is computed over that exact string.
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="PUBLIC_BASE_URL not configured")
    url = f"{base}{request.url.path}"

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    if not validator.validate(url, form, signature):
        log.warning("Rejected webhook with bad Twilio signature (url=%s)", url)
        raise HTTPException(status_code=403, detail="invalid signature")


@router.post("/twilio")
async def twilio_inbound(request: Request) -> Response:
    form = dict(await request.form())
    await _verify_signature(request, form)

    sender = form.get("From", "")
    body = (form.get("Body") or "").strip()

    if _same_number(sender, settings.TWILIO_WHATSAPP_TO):
        await _handle_diego(body)
    elif settings.TWILIO_WHATSAPP_DANIEL and _same_number(
        sender, settings.TWILIO_WHATSAPP_DANIEL
    ):
        await _handle_daniel(body)
    else:
        log.info("Ignoring message from unknown sender %s", sender)

    return Response(content=_EMPTY_TWIML, media_type="application/xml")


async def _handle_diego(body: str) -> None:
    url = xverify.extract_post_url(body)
    if not url:
        log.info("Message from Diego with no post URL; ignoring")
        return

    if not await xverify.post_exists(url):
        log.warning("Post URL failed the existence check: %s", url)
        await asyncio.to_thread(
            service._notify,
            settings.TWILIO_WHATSAPP_TO,
            "⚠️ That link doesn't resolve to a public post. Nothing was logged.",
            "Diego (bad link)",
        )
        return

    await asyncio.to_thread(_record_post, url)


def _record_post(url: str) -> None:
    now = ledger.utcnow()
    day = judge.local_date(now)

    with SessionLocal() as db:
        written = ledger.append(
            db, EventType.POST_LOGGED, day, {"url": url}, occurred_at=now
        )

    if written is None:
        # Already logged today. The first submission is the one that counts —
        # a later one must never overwrite an earlier (possibly on-time) entry.
        log.info("Post already logged for %s; ignoring resubmission", day)
        _reply(f"Already logged for today. The first submission stands.")
        return

    on_time = judge.to_local(now) <= judge.deadline_at(day)
    log.info("POST_LOGGED for %s (on_time=%s): %s", day, on_time, url)
    _reply(
        "✅ Logged. You're inside the deadline."
        if on_time
        else "⚠️ Logged, but this is after 2 PM. Today is already a miss."
    )


def _reply(text: str) -> None:
    try:
        send_whatsapp(text, to=settings.TWILIO_WHATSAPP_TO)
    except Exception as e:
        log.error("Could not acknowledge to Diego: %s", e)


async def _handle_daniel(body: str) -> None:
    if not CLAIM_PATTERN.search(body):
        log.info("Message from Daniel with no claim keyword; ignoring")
        return
    await asyncio.to_thread(_claim_debt)


def _claim_debt() -> None:
    now = ledger.utcnow()

    with SessionLocal() as db:
        day = service.open_debt_day(db, now)

        if day is None:
            log.info("Daniel tried to claim, but no open debt exists")
            service._notify(
                settings.TWILIO_WHATSAPP_DANIEL,
                "No open debt to claim right now.",
                "Daniel (no debt)",
            )
            return

        written = ledger.append(db, EventType.DEBT_CLAIMED, day, {"claimed_for": str(day)})
        if written is None:
            log.info("Debt for %s was already claimed", day)
            return

        streak = ledger.current_streak(db, judge.local_date(now))
        log.info("Debt for %s claimed by Daniel", day)

        service._notify(
            settings.TWILIO_WHATSAPP_DANIEL,
            messages.compose_debt_claimed(streak),
            "Daniel (debt claimed)",
        )
        service._notify(
            settings.TWILIO_WHATSAPP_TO,
            f"💸 Daniel claimed the 200 MXN for {day}. Pay up.",
            "Diego (debt claimed)",
        )
