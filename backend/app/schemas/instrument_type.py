from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InstrumentTypeBase(BaseModel):
    type_code: str = Field(..., max_length=50)
    type_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    measurement_unit: str = Field(..., max_length=50)
    default_calibration_interval_days: int = Field(default=90, ge=1)
    default_tolerance: float = Field(default=2.0, ge=0.0)
    is_active: bool = True


class InstrumentTypeCreate(InstrumentTypeBase):
    pass


class InstrumentTypeUpdate(BaseModel):
    type_name: Optional[str] = None
    description: Optional[str] = None
    measurement_unit: Optional[str] = None
    default_calibration_interval_days: Optional[int] = Field(None, ge=1)
    default_tolerance: Optional[float] = Field(None, ge=0.0)
    is_active: Optional[bool] = None


class InstrumentTypeOut(InstrumentTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
