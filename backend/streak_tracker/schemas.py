from pydantic import BaseModel
from datetime import datetime


class Commit(BaseModel):
    title:str
    diff:str

class PushEvent(BaseModel):
    timestamp: datetime
    commits:list[Commit]
    repo_name: str
    streak_count: int
