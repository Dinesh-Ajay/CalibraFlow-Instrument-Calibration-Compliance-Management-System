from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CalibrationPlanBase(BaseModel):
    instrument_type_id: int
    calibration_interval_days: int = Field(default=90, ge=1)
    tolerance: float = Field(default=2.0, ge=0.0)
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    due_date_calculation_method: str = "CALENDAR_DAYS"
    grace_period_days: int = Field(default=0, ge=0)
    certificate_required: bool = True
    emergency_extension_allowed: bool = True
    status: str = "ACTIVE"


class CalibrationPlanCreate(CalibrationPlanBase):
    asset_id: Optional[int] = None
    plan_code: Optional[str] = None
    plan_name: Optional[str] = None
    # Frontend compatibility aliases
    interval_months: Optional[int] = Field(default=None, ge=1)
    tolerance_percentage: Optional[float] = Field(default=None, ge=0.0)
    calculation_method: Optional[str] = None


class CalibrationPlanUpdate(BaseModel):
    calibration_interval_days: Optional[int] = Field(None, ge=1)
    tolerance: Optional[float] = Field(None, ge=0.0)
    effective_until: Optional[datetime] = None
    grace_period_days: Optional[int] = Field(None, ge=0)
    certificate_required: Optional[bool] = None
    emergency_extension_allowed: Optional[bool] = None
    status: Optional[str] = None


class CalibrationPlanOut(CalibrationPlanBase):
    id: int
    plan_code: str
    asset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    instrument_type_name: Optional[str] = None
    plan_name: Optional[str] = None

    class Config:
        from_attributes = True


class AssetBase(BaseModel):
    asset_name: str = Field(..., max_length=255)
    instrument_type_id: int
    serial_number: str = Field(..., max_length=100)
    manufacturer: str = Field(..., max_length=100)
    model_number: str = Field(..., max_length=100)
    plant_location: str = Field(..., max_length=100)
    production_line: str = Field(..., max_length=100)
    installation_date: Optional[datetime] = None
    commissioning_date: Optional[datetime] = None
    calibration_interval_days: int = Field(default=90, ge=1)
    requires_calibration: bool = True
    requires_certificate: bool = True
    supplier_id: Optional[int] = None


class AssetCreate(AssetBase):
    custom_tolerance: Optional[float] = None
    last_calibration_date: Optional[datetime] = None


class AssetUpdate(BaseModel):
    asset_name: Optional[str] = None
    plant_location: Optional[str] = None
    production_line: Optional[str] = None
    calibration_interval_days: Optional[int] = Field(None, ge=1)
    operational_status: Optional[str] = None
    requires_calibration: Optional[bool] = None
    requires_certificate: Optional[bool] = None
    instrument_type_id: Optional[int] = None


class AssetOut(AssetBase):
    id: int
    asset_code: str
    last_calibration_date: Optional[datetime] = None
    next_due_date: Optional[datetime] = None
    operational_status: str
    calibration_status: str
    created_at: datetime
    updated_at: datetime
    instrument_type_name: Optional[str] = None

    class Config:
        from_attributes = True
