"""TwiML endpoint Twilio fetches when the Overseer places a call. It reads the
`msg` back to Diego. (Swap voice/language here if you compose messages in Spanish.)"""

from xml.sax.saxutils import escape

from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/voice/twiml")
def voice_twiml(msg: str = "You missed a deadline. Handle it.") -> Response:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Say voice="Polly.Joanna" language="en-US">{escape(msg)}</Say>'
        '</Response>'
    )
    return Response(content=xml, media_type="application/xml")
