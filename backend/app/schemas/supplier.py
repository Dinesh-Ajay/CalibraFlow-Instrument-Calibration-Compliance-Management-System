from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SupplierBase(BaseModel):
    supplier_name: str = Field(..., max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    accreditation_reference: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="ACTIVE")


class SupplierCreate(SupplierBase):
    supplier_code: Optional[str] = None


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    accreditation_reference: Optional[str] = None
    status: Optional[str] = None


class SupplierOut(SupplierBase):
    id: int
    supplier_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
