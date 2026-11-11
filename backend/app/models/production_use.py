from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ProductionUse(Base):
    __tablename__ = "production_uses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usage_code = Column(String(100), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    production_line = Column(String(100), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    usage_timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    usage_end_timestamp = Column(DateTime, nullable=True)
    usage_status = Column(String(50), default="RECORDED", nullable=False)  # RECORDED, COMPLETED, INTERRUPTED
    validation_decision = Column(String(50), nullable=False, index=True)  # ALLOWED, ALLOWED_WITH_EXCEPTION, BLOCKED
    decision_reason = Column(Text, nullable=False)
    calibration_event_id = Column(Integer, ForeignKey("calibration_events.id"), nullable=True, index=True)
    exception_id = Column(Integer, ForeignKey("emergency_extensions.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    asset = relationship("Asset", back_populates="production_uses")
    operator = relationship("User", back_populates="production_uses")
    calibration_event = relationship("CalibrationEvent", back_populates="production_uses")
    emergency_extension = relationship("EmergencyExtension", back_populates="production_uses")
