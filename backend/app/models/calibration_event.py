from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class CalibrationEvent(Base):
    __tablename__ = "calibration_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    calibration_code = Column(String(100), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    calibration_plan_id = Column(Integer, ForeignKey("calibration_plans.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True, index=True)
    calibration_date = Column(DateTime, default=utcnow, nullable=False, index=True)
    previous_due_date = Column(DateTime, nullable=True)
    calculated_next_due_date = Column(DateTime, nullable=True)
    measured_value = Column(Float, nullable=False)
    reference_value = Column(Float, nullable=False)
    measurement_error = Column(Float, nullable=False)
    tolerance = Column(Float, nullable=False)
    result = Column(String(50), nullable=False, index=True)  # PASS, FAIL, CONDITIONAL
    calibration_status = Column(String(50), default="COMPLETED", nullable=False)  # COMPLETED, PENDING_REVIEW, REJECTED
    performed_by = Column(String(100), nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    certificate_required = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    asset = relationship("Asset", back_populates="calibration_events")
    calibration_plan = relationship("CalibrationPlan", back_populates="calibration_events")
    supplier = relationship("Supplier", back_populates="calibration_events")
    work_order = relationship("WorkOrder", back_populates="calibration_events")
    certificates = relationship("Certificate", back_populates="calibration_event", cascade="all, delete-orphan")
    corrective_actions = relationship("CorrectiveAction", back_populates="calibration_event")
    impact_assessments = relationship("ImpactAssessment", back_populates="calibration_event")
    production_uses = relationship("ProductionUse", back_populates="calibration_event")
    alerts = relationship("Alert", back_populates="calibration_event")
