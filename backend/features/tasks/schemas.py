from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class UserTaskCreate(BaseModel):
    task_name: str
    task_source: str
    finish_criteria: str
    deadline: datetime
    notification_channel: Literal["whatsapp", "telegram"]


class UserTask(UserTaskCreate):
    id: int



