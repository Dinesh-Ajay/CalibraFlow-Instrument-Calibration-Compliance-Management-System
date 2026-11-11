from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class CalibrationPlan(Base):
    __tablename__ = "calibration_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True)
    instrument_type_id = Column(Integer, ForeignKey("instrument_types.id"), nullable=False, index=True)
    calibration_interval_days = Column(Integer, nullable=False, default=90)
    tolerance = Column(Float, nullable=False, default=2.0)
    effective_from = Column(DateTime, default=utcnow, nullable=False)
    effective_until = Column(DateTime, nullable=True)
    due_date_calculation_method = Column(String(50), default="CALENDAR_DAYS", nullable=False)
    grace_period_days = Column(Integer, default=0, nullable=False)
    certificate_required = Column(Boolean, default=True, nullable=False)
    emergency_extension_allowed = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)  # ACTIVE, SUPERSEDED, INACTIVE
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    asset = relationship("Asset", back_populates="calibration_plans")
    instrument_type = relationship("InstrumentType", back_populates="calibration_plans")
    calibration_events = relationship("CalibrationEvent", back_populates="calibration_plan")
    work_orders = relationship("WorkOrder", back_populates="calibration_plan")
