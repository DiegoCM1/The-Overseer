from google.adk import Agent

import datetime 
from zoneinfo import ZoneInfo


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specificied city
    
    Args: 
        city (str): The name of the city to retrieve the weather report.
    
    Returns: 
        dict: Status and result or error message.
    """
    if city.lower() == "mexico city":
        return {
            "status": "ok",
            "report": (
                "The weather in Mexico City is sunny and great to work at a wonderful company"
            ),
        }
    else: 
        return {
            "status": "error",
            "error_message": f"Weather information for {city} not available"
        }


def get_current_time(city: str):
    """Returns the current time in a specified city
    
    Args:
        city (str): City of which the time is going to be retrieved

    Returns:
        dict: status and result or error message
    """

    if city.lower() == "mexico city":
        tz_identifier = "America/Mexico_City"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}"
            )
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f"The current time im {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}"
    )
    return {
        "status": "success",
        "report": "report"
    }


# AGENT DEFINITION
root_agent = Agent(
    name="crazy_assistant",
    model="gemini-3.6-flash",
    instruction="You are a helpful assistant that can answer questions with a fun and sarcastic tone.",
    tools=[get_weather, get_current_time]
)

