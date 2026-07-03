from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.role import RoleResponse


# ==========================================
# AUTH SCHEMAS
# ==========================================

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role_name: str
    organization_id: int


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None


# ==========================================
# USER MANAGEMENT SCHEMAS
# ==========================================

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role_name: str
    organization_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150
    )
    email: Optional[EmailStr] = None
    role_name: Optional[str] = None


class PasswordResetResponse(BaseModel):
    message: str


# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    organization_id: int
    is_active: bool
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True