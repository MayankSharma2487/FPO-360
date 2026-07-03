from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FarmerBase(BaseModel):
    farmer_name: str = Field(..., min_length=2, max_length=150)
    mobile_number: str = Field(..., min_length=10, max_length=15)
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    aadhaar_number: Optional[str] = None
    photo_url: Optional[str] = None
    shareholder_no: Optional[str] = None
    land_holding_acres: Optional[float] = None
    farmer_category: Optional[str] = None
    is_shareholder: bool = False
    village_id: Optional[int] = None


class FarmerCreate(FarmerBase):
    farmer_code: Optional[str] = None
    organization_id: Optional[int] = None


class FarmerUpdate(BaseModel):
    farmer_name: Optional[str] = None
    mobile_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    aadhaar_number: Optional[str] = None
    photo_url: Optional[str] = None
    shareholder_no: Optional[str] = None
    land_holding_acres: Optional[float] = None
    farmer_category: Optional[str] = None
    is_shareholder: Optional[bool] = None
    village_id: Optional[int] = None
    is_active: Optional[bool] = None


class FarmerResponse(FarmerBase):
    id: int
    farmer_code: str
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    village_name: Optional[str] = None

    class Config:
        from_attributes = True