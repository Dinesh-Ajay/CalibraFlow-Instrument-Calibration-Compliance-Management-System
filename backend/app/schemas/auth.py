from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    roles: List[str] = []


class RoleOut(BaseModel):
    id: int
    role_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    roles: List[str] = []
    role_ids: List[int] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


Token.model_rebuild()
