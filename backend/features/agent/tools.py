import ast
import operator
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


# Safe arithmetic only — no eval(). The model can't reach names, calls, or
# attributes, so a hostile expression can't run code.
_MATH_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _MATH_OPS:
        return _MATH_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _MATH_OPS:
        return _MATH_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("unsupported expression")


def do_math(expression: str):
    try:
        return str(_eval_node(ast.parse(expression, mode="eval").body))
    except Exception:
        return "error: only basic arithmetic is supported"


def send_whatsapp(message: str):
    # Numbers come from settings now, not hardcoded.
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            body=message,
            to=settings.TWILIO_WHATSAPP_TO,
        )
        return "sent"
    except TwilioRestException as e:
        return f"Twilio error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# DEBUGGING/TESTING
# print(do_math("2*2*2*5"))
# print (get_current_datetime('Asia/Tokyo')) #Debug
# print(send_whatsapp("Hi, how you fucking doing? 3"))





