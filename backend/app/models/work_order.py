from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    work_order_code = Column(String(100), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    calibration_plan_id = Column(Integer, ForeignKey("calibration_plans.id"), nullable=True, index=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    priority = Column(String(50), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    work_order_type = Column(String(50), default="CALIBRATION", nullable=False)  # CALIBRATION, MAINTENANCE, CORRECTIVE, EMERGENCY
    description = Column(Text, nullable=True)
    scheduled_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=True)
    completion_time = Column(DateTime, nullable=True)
    downtime_minutes = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False, index=True)  # OPEN, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, ON_HOLD
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    asset = relationship("Asset", back_populates="work_orders")
    calibration_plan = relationship("CalibrationPlan", back_populates="work_orders")
    assignee = relationship("User", back_populates="work_orders_assigned")
    calibration_events = relationship("CalibrationEvent", back_populates="work_order")
    alerts = relationship("Alert", back_populates="work_order")
