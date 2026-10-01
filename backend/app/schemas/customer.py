from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=150)
    mobile_number: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)


class CustomerCreate(CustomerBase):
    organization_id: Optional[int] = None


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=150)
    mobile_number: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: int
    customer_code: str
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
