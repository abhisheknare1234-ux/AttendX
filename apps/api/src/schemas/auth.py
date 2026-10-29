from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from apps.api.src.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    roll_number: Optional[str] = None
    prn: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = "Artificial Intelligence & Data Science"


class UserResponse(UserBase):
    id: str
    is_active: bool
    roll_number: Optional[str] = None
    prn: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    is_biometric_enrolled: Optional[bool] = None

    class Config:
        from_attributes = True


class AdminBootstrapRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = "Institutional"
    last_name: str = "Administrator"

