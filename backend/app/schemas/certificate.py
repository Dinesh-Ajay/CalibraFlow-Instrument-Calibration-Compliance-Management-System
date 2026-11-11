from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CertificateCreate(BaseModel):
    calibration_event_id: int
    asset_id: int
    supplier_id: Optional[int] = None
    certificate_number: str = Field(..., max_length=100)
    issue_date: datetime
    expiry_date: datetime


class CertificateVerifyRequest(BaseModel):
    verification_status: str  # VERIFIED, REJECTED, INVALID
    notes: Optional[str] = None


class CertificateOut(BaseModel):
    id: int
    certificate_code: str
    calibration_event_id: int
    asset_id: int
    supplier_id: Optional[int] = None
    certificate_number: str
    file_path: Optional[str] = None
    issue_date: datetime
    expiry_date: datetime
    verification_status: str
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    class Config:
        from_attributes = True
