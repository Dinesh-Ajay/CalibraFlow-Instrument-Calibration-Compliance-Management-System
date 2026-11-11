from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductionValidateRequest(BaseModel):
    asset_id: int
    production_line: str = Field(..., max_length=100)
    usage_timestamp: Optional[datetime] = None
    # Optional frontend metadata (not used for authorization/decision override)
    operator_id: Optional[str] = None
    batch_id: Optional[str] = None
    planned_use_timestamp: Optional[datetime] = None


class ProductionValidateResponse(BaseModel):
    asset_id: int
    asset_code: str
    asset_name: str
    decision: str  # ALLOWED, ALLOWED_WITH_EXCEPTION, BLOCKED
    decision_reason: str
    applicable_due_date: Optional[datetime] = None
    certificate_status: Optional[str] = None
    exception_reference: Optional[str] = None
    last_calibration_date: Optional[datetime] = None
    is_allowed: bool


class ProductionUseRecordRequest(BaseModel):
    asset_id: int
    production_line: str = Field(..., max_length=100)
    usage_timestamp: Optional[datetime] = None
    usage_end_timestamp: Optional[datetime] = None
    usage_status: str = "RECORDED"
    override_reason: Optional[str] = None
    # Optional frontend metadata (ignored by backend for security)
    operator_id: Optional[str] = None
    batch_id: Optional[str] = None
    use_timestamp: Optional[datetime] = None


class ProductionUseOut(BaseModel):
    id: int
    usage_code: str
    asset_id: int
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    production_line: str
    operator_id: int
    operator_name: Optional[str] = None
    usage_timestamp: datetime
    usage_end_timestamp: Optional[datetime] = None
    usage_status: str
    validation_decision: str
    decision_reason: str
    calibration_event_id: Optional[int] = None
    exception_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
