from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_code = Column(String(100), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    related_calibration_id = Column(Integer, ForeignKey("calibration_events.id"), nullable=True, index=True)
    related_work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    # Types: UPCOMING_CALIBRATION, OVERDUE_CALIBRATION, FAILED_CALIBRATION, MISSING_CERTIFICATE, INVALID_CERTIFICATE, PROHIBITED_USAGE, IMPACT_ASSESSMENT_REQUIRED
    severity = Column(String(50), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False, index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    generated_at = Column(DateTime, default=utcnow, nullable=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    asset = relationship("Asset", back_populates="alerts")
    calibration_event = relationship("CalibrationEvent", back_populates="alerts")
    work_order = relationship("WorkOrder", back_populates="alerts")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
