from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CorrectiveActionCreate(BaseModel):
    calibration_event_id: int
    asset_id: int
    description: str
    assigned_to: Optional[int] = None
    root_cause: Optional[str] = None


class CorrectiveActionUpdate(BaseModel):
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    status: Optional[str] = None  # OPEN, IN_PROGRESS, RESOLVED, CLOSED


class CorrectiveActionOut(BaseModel):
    id: int
    corrective_action_code: str
    calibration_event_id: int
    asset_id: int
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    description: str
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None
    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImpactAssessmentCreate(BaseModel):
    calibration_event_id: int
    asset_id: int
    affected_production_start: Optional[datetime] = None
    affected_production_end: Optional[datetime] = None
    affected_usage_count: Optional[int] = Field(default=0, ge=0)
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    assessment_notes: Optional[str] = None


class ImpactAssessmentUpdate(BaseModel):
    affected_production_start: Optional[datetime] = None
    affected_production_end: Optional[datetime] = None
    affected_usage_count: Optional[int] = None
    risk_level: Optional[str] = None
    assessment_notes: Optional[str] = None
    status: Optional[str] = None  # PENDING, COMPLETED


class ImpactAssessmentOut(BaseModel):
    id: int
    assessment_code: str
    calibration_event_id: int
    asset_id: int
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    affected_production_start: Optional[datetime] = None
    affected_production_end: Optional[datetime] = None
    affected_usage_count: int
    risk_level: str
    assessment_notes: Optional[str] = None
    assessed_by: Optional[int] = None
    assessor_name: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmergencyExtensionCreate(BaseModel):
    asset_id: int
    extended_due_date: datetime
    reason: str


class EmergencyExtensionDecision(BaseModel):
    approved: bool = True
    notes: Optional[str] = None


class EmergencyExtensionOut(BaseModel):
    id: int
    extension_code: str
    asset_id: int
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    original_due_date: datetime
    extended_due_date: datetime
    reason: str
    requested_by: Optional[int] = None
    requester_name: Optional[str] = None
    approved_by: Optional[int] = None
    approver_name: Optional[str] = None
    approval_status: str
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
