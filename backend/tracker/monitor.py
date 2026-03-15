from datetime import datetime
import time
import subprocess
import json
from tracker.schemas import BrowserEvent
from pathlib import Path 

# Defining what is the json.
BLACKLIST_PATH = Path(__file__).parent.parent / "core" / "blacklist.json"


def load_blacklist():
    try: 
        with open(BLACKLIST_PATH, 'r') as file:
            # Convert JSON into dict
            json_file = json.load(file)
            blacklist = json_file["sites"]
            print(f"Retrieved json: {json_file}")
            print(f"Retrieved blacklist: {blacklist}")

            return blacklist

    
    except FileNotFoundError:
        return []

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
    browser = "Chrome"

    if not url or not title:
        return None, None # Return empty values if not used 

    return url, title, browser

# Main function
def start_monitoring():
    start_time = None
    new_url_start_time = None
    last_url = None
    duration = 0
    active_tab_title = None

    sleep_time = 5

    # Read blacklist
    blacklist = load_blacklist()
    
    while True:
        # Get browser data
        url, title, browser = get_browser_data()
        print("Got url: " + url + " and title: " + title)

        # If invalid values
        if url is None or title is None:
            print("Url or title is None, skipping exectution")
            duration = 0
            last_url = None
            start_time = None
            time.sleep(60)
            continue

        # URL in blacklist
        if url in blacklist: 
            print("Url in blacklist!")
            url_in_blacklist = True
            # Not the same URL
            if last_url != url:
                start_time = datetime.now()
                last_url = url
            # Same URL
            else:
                # Calculate duration based on start time
                new_url_start_time = datetime.now()
                duration = new_url_start_time - start_time
                last_url = url 
            
            event = BrowserEvent(
                active_url=url,
                start_time=start_time,
                duration_seconds=duration,
                url_in_blacklist=url_in_blacklist,
                active_tab_title=title,
                browser=browser,
            )
        
        time.sleep(sleep_time)
        print(f"Sleeping for {sleep_time} seconds")


start_monitoring()
        
# Security/Stability for importing
if __name__ == "__main__":
    main()