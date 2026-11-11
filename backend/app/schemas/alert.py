from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertOut(BaseModel):
    id: int
    alert_code: str
    asset_id: int
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    related_calibration_id: Optional[int] = None
    related_work_order_id: Optional[int] = None
    alert_type: str
    severity: str
    message: str
    status: str
    generated_at: datetime
    acknowledged_by: Optional[int] = None
    acknowledged_by_name: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class AlertResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None
