"""Twilio delivery: WhatsApp (working today), SMS, and voice calls.

All three raise on failure so the caller (the tick) can decide whether to record
the step or leave it for the next poll to retry.
"""

from urllib.parse import quote

from twilio.rest import Client

from core.config import settings


def _client() -> Client:
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_whatsapp(body: str, to: str | None = None):
    return _client().messages.create(
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=to or settings.TWILIO_WHATSAPP_TO,
        body=body,
    )


def send_sms(body: str, to: str | None = None):
    return _client().messages.create(
        from_=settings.TWILIO_SMS_FROM,
        to=to or settings.MY_PHONE,
        body=body,
    )


def make_call(message: str, to: str | None = None):
    # Twilio fetches TwiML from our own service, which reads back `message`.
    twiml_url = f"{settings.PUBLIC_BASE_URL}/voice/twiml?msg={quote(message)}"
    return _client().calls.create(
        from_=settings.TWILIO_VOICE_FROM,
        to=to or settings.MY_PHONE,
        url=twiml_url,
    )
