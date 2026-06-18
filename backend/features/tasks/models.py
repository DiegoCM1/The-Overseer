import enum
from core.db import Base
from sqlalchemy import Integer, String, DateTime, Column, Enum

class Channel(enum.Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

class Tasks(Base):
    __tablename__ = "tasks"
    id = Column(Integer, nullable=False, primary_key=True)
    task_name = Column(String, nullable=False)
    task_source = Column(String, nullable=False)
    finish_criteria = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    notification_channel = Column(Enum(Channel), nullable=False)