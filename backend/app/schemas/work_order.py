from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WorkOrderCreate(BaseModel):
    asset_id: int
    calibration_plan_id: Optional[int] = None
    assigned_to: Optional[int] = None
    priority: str = "MEDIUM"
    work_order_type: str = "CALIBRATION"
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    # Frontend compatibility aliases
    planned_downtime_minutes: Optional[int] = Field(default=None, ge=0)
    scheduled_start: Optional[datetime] = None


class WorkOrderStatusUpdate(BaseModel):
    status: str  # OPEN, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, ON_HOLD
    assigned_to: Optional[int] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    downtime_minutes: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    # Frontend compatibility
    actual_downtime_minutes: Optional[int] = Field(None, ge=0)


class WorkOrderOut(BaseModel):
    id: int
    work_order_code: str
    asset_id: int
    calibration_plan_id: Optional[int] = None
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None
    priority: str
    work_order_type: str
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    downtime_minutes: int
    status: str
    created_at: datetime
    updated_at: datetime
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    class Config:
        from_attributes = True
