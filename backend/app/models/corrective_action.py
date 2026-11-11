from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    corrective_action_code = Column(String(100), unique=True, nullable=False, index=True)
    calibration_event_id = Column(Integer, ForeignKey("calibration_events.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    root_cause = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    status = Column(String(50), default="OPEN", nullable=False, index=True)  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    opened_at = Column(DateTime, default=utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    calibration_event = relationship("CalibrationEvent", back_populates="corrective_actions")
    asset = relationship("Asset", back_populates="corrective_actions")
    assignee = relationship("User", foreign_keys=[assigned_to])
