from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    accreditation_reference = Column(String(100), nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    calibration_events = relationship("CalibrationEvent", back_populates="supplier")
    certificates = relationship("Certificate", back_populates="supplier")
