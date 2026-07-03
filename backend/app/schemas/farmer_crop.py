from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FarmerCropBase(BaseModel):
    season: Optional[str] = None
    year: int
    area_acres: Optional[float] = None
    sowing_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    expected_yield: Optional[float] = None
    actual_yield: Optional[float] = None
    remarks: Optional[str] = None


class FarmerCropCreate(FarmerCropBase):
    farmer_id: int
    crop_id: int
    organization_id: Optional[int] = None


class FarmerCropUpdate(BaseModel):
    season: Optional[str] = None
    area_acres: Optional[float] = None
    sowing_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    expected_yield: Optional[float] = None
    actual_yield: Optional[float] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class FarmerCropResponse(FarmerCropBase):
    id: int
    farmer_id: int
    crop_id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    farmer_name: Optional[str] = None
    crop_name: Optional[str] = None

    class Config:
        from_attributes = True