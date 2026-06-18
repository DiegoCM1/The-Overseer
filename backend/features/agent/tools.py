from datetime import datetime
from zoneinfo import ZoneInfo
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from core.config import settings



# TOOL DEFINITIONS
tools = [
    {
        "type": "function",
        "name": "get_current_datetime",
        "description": "Obtain current date and time",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Something like America/Los_Angeles or Asia/Tokyo"
                },
            },
            "required": ["timezone"],
        },
    }, 
        {
        "type": "function",
        "name": "do_math",
        "description": "Obtain results to mathematical expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression"
                },
            },
            "required": ["expression"],
        },
    }, 
        {
        "type": "function",
        "name": "send_whatsapp",
        "description": "Send a message using WA",
        "parameters": {
            "type": "object",
            "properties": {
                "whatsapp_message": {
                    "type": "string",
                    "description": "Anything you want to say to the user over WhatsApp"
                },
            },
            "required": ["whatsapp_message"],
        },
    }, 
]


def get_current_datetime(timezone):
    current_timezone = ZoneInfo(timezone)
    current_time = datetime.now(current_timezone)
    string_current_time = str(current_time)

    return string_current_time


def do_math(expression:str):
    result = eval(expression)
    result_str = str(result)
    return result_str


def send_whatsapp(message:str):
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        client = Client(account_sid, auth_token)

        response = client.messages.create(
        from_='whatsapp:+14155238886',
        body=message,
        to='whatsapp:+5217151459328'
        )
    except TwilioRestException as e:
        return f"Twilio error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# DEBUGGING/TESTING
# print(do_math("2*2*2*5"))
# print (get_current_datetime('Asia/Tokyo')) #Debug
# print(send_whatsapp("Hi, how you fucking doing? 3"))





