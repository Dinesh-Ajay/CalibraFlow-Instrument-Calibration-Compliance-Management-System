from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    certificate_code = Column(String(100), unique=True, nullable=False, index=True)
    calibration_event_id = Column(Integer, ForeignKey("calibration_events.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    certificate_number = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=True)
    issue_date = Column(DateTime, default=utcnow, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    verification_status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, VERIFIED, REJECTED, INVALID
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    calibration_event = relationship("CalibrationEvent", back_populates="certificates")
    asset = relationship("Asset", back_populates="certificates")
    supplier = relationship("Supplier", back_populates="certificates")
