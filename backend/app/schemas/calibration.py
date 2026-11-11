from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CalibrationScheduleRequest(BaseModel):
    asset_id: int
    scheduled_date: Optional[datetime] = None
    priority: str = "MEDIUM"
    assigned_to: Optional[int] = None
    notes: Optional[str] = None


class CalibrationEventCreate(BaseModel):
    asset_id: int
    calibration_plan_id: Optional[int] = None
    supplier_id: Optional[int] = None
    work_order_id: Optional[int] = None
    calibration_date: Optional[datetime] = None
    measured_value: float
    reference_value: float
    tolerance: Optional[float] = None
    performed_by: str = Field(..., max_length=100)
    reviewed_by: Optional[str] = None
    certificate_required: bool = True
    notes: Optional[str] = None


class CalibrationEventOut(BaseModel):
    id: int
    calibration_code: str
    asset_id: int
    calibration_plan_id: int
    supplier_id: Optional[int] = None
    work_order_id: Optional[int] = None
    calibration_date: datetime
    previous_due_date: Optional[datetime] = None
    calculated_next_due_date: Optional[datetime] = None
    measured_value: float
    reference_value: float
    measurement_error: float
    tolerance: float
    result: str
    calibration_status: str
    performed_by: str
    reviewed_by: Optional[str] = None
    certificate_required: bool
    notes: Optional[str] = None
    created_at: datetime
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    class Config:
        from_attributes = True
