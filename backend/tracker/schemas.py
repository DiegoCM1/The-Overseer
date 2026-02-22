from pydantic import BaseModel
from datetime import datetime

class BrowserEvent(BaseModel):
    active_url: str
    start_time: datetime # The moment the polling detects a brand new url in the browser       
    duration_seconds: float # If the url is brand new, send 0 here, if the url is like the previous event, then calculate seconds from start_time up to this last poll
    url_in_blacklist: bool
    active_tab_title: str
    browser: str
