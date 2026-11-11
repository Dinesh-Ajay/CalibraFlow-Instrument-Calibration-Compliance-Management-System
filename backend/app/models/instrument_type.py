from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class InstrumentType(Base):
    __tablename__ = "instrument_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_code = Column(String(50), unique=True, nullable=False, index=True)
    type_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    measurement_unit = Column(String(50), nullable=False)
    default_calibration_interval_days = Column(Integer, nullable=False, default=90)
    default_tolerance = Column(Float, nullable=False, default=2.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    assets = relationship("Asset", back_populates="instrument_type")
    calibration_plans = relationship("CalibrationPlan", back_populates="instrument_type")
