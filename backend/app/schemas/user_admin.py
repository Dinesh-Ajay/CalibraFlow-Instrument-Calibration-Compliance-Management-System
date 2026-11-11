from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    role_ids: List[int] = Field(default_factory=list)
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)


class AssignRolesRequest(BaseModel):
    role_ids: List[int] = Field(default_factory=list)


class UserActivityItem(BaseModel):
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    reason: Optional[str] = None
