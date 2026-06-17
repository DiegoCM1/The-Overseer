from datetime import datetime
from zoneinfo import ZoneInfo


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


# DEBUGGING/TESTING
# print(do_math("2*2*2*5"))
# print (get_current_datetime('Asia/Tokyo')) #Debug





