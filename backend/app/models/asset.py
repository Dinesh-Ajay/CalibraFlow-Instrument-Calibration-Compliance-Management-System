from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_code = Column(String(50), unique=True, nullable=False, index=True)
    asset_name = Column(String(255), nullable=False, index=True)
    instrument_type_id = Column(Integer, ForeignKey("instrument_types.id"), nullable=False, index=True)
    serial_number = Column(String(100), nullable=False)
    manufacturer = Column(String(100), nullable=False)
    model_number = Column(String(100), nullable=False)
    plant_location = Column(String(100), nullable=False)
    production_line = Column(String(100), nullable=False, index=True)
    installation_date = Column(DateTime, nullable=True)
    commissioning_date = Column(DateTime, nullable=True)
    calibration_interval_days = Column(Integer, nullable=False, default=90)
    last_calibration_date = Column(DateTime, nullable=True)
    next_due_date = Column(DateTime, nullable=True, index=True)
    operational_status = Column(String(50), default="ACTIVE", nullable=False, index=True)  # ACTIVE, INACTIVE, RESTRICTED, MAINTENANCE, RETIRED
    calibration_status = Column(String(50), default="COMPLIANT", nullable=False, index=True)  # COMPLIANT, UPCOMING, OVERDUE, FAILED, PENDING_CERTIFICATE
    requires_calibration = Column(Boolean, default=True, nullable=False)
    requires_certificate = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    instrument_type = relationship("InstrumentType", back_populates="assets")
    calibration_plans = relationship("CalibrationPlan", back_populates="asset", cascade="all, delete-orphan")
    calibration_events = relationship("CalibrationEvent", back_populates="asset")
    certificates = relationship("Certificate", back_populates="asset")
    work_orders = relationship("WorkOrder", back_populates="asset")
    production_uses = relationship("ProductionUse", back_populates="asset")
    alerts = relationship("Alert", back_populates="asset")
    corrective_actions = relationship("CorrectiveAction", back_populates="asset")
    impact_assessments = relationship("ImpactAssessment", back_populates="asset")
    emergency_extensions = relationship("EmergencyExtension", back_populates="asset")
