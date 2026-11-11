from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class EmergencyExtension(Base):
    __tablename__ = "emergency_extensions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    extension_code = Column(String(100), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    original_due_date = Column(DateTime, nullable=False)
    extended_due_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, EXPIRED
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    asset = relationship("Asset", back_populates="emergency_extensions")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    production_uses = relationship("ProductionUse", back_populates="emergency_extension")
