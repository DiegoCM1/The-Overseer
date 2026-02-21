from datetime import datetime
import time
import subprocess
import json
from tracker.schemas import BrowserEvent


def get_browser_data():
    # Call applescript
    result_url = subprocess.run(
        ["osascript", "-e", 'tell application "Google Chrome" to get URL of active tab of front window'],
        capture_output=True,
        text=True
    )

    result_title = subprocess.run(
        ["osascript", "-e", 'tell application "Google Chrome" to get Title of active tab of front window'],
        capture_output=True,
        text=True
    )

    url = result_url.stdout.strip()
    title = result_title.stdout.strip()

    if not url or not title:
        return None, None # Finish the

    return url, title

# Defining what is the json.
blacklist = '../core/blacklist.json'

def load_blacklist():
    try: 
        with open(blacklist, 'r') as file:
            # Convert JSON into dict
            return json.load(file)

# Main function
def start_monitoring():
    start_time = None
    last_url = None

    # Read blacklist

    while True:
        get_browser_data():

        if url







# start_time = none
# last_url = none

#     while true:
#         # Apple script
#         Call applescript, obtain required data fields.

#         # Decision logic. 
#         If URL in blacklist:
#             check if new url
#             if new url:
#                 duration 0
#                 start_time now
#             else:
#                 calculate duration based on start_time
#                 update last_url
#             send browser event
#         else:
#             duration = 0
#             update last url

#         #Sleep 60 s
        
