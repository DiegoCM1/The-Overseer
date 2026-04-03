
from twilio.rest import Client
from core.config import settings



def send_whatsapp_message(message: str) -> None:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        response = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            body=message,
            to=settings.TWILIO_WHATSAPP_TO,
        )
        print(response.sid)

    except Exception as e:
        print(f"Failed to send message: {e}")