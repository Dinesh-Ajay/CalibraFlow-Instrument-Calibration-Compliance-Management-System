from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ImpactAssessment(Base):
    __tablename__ = "impact_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_code = Column(String(100), unique=True, nullable=False, index=True)
    calibration_event_id = Column(Integer, ForeignKey("calibration_events.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    affected_production_start = Column(DateTime, nullable=True)
    affected_production_end = Column(DateTime, nullable=True)
    affected_usage_count = Column(Integer, default=0, nullable=False)
    risk_level = Column(String(50), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    assessment_notes = Column(Text, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, COMPLETED
    created_at = Column(DateTime, default=utcnow, nullable=False)

    calibration_event = relationship("CalibrationEvent", back_populates="impact_assessments")
    asset = relationship("Asset", back_populates="impact_assessments")
    assessor = relationship("User", foreign_keys=[assessed_by])
