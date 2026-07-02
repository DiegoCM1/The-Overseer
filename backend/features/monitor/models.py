"""Audit + idempotency for escalation. One row per (date, goal, level) that has
already fired — the unique constraint is what stops the Overseer re-nagging."""

from sqlalchemy import Column, Date, DateTime, Integer, String, UniqueConstraint, func

from core.db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    log_date = Column(Date, nullable=False)
    goal_id = Column(String, nullable=False)
    level = Column(Integer, nullable=False)      # 1 = nudge, 2 = firmer, 3 = call
    channel = Column(String, nullable=False)     # whatsapp | sms | call
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("log_date", "goal_id", "level", name="uq_notification_step"),
    )
