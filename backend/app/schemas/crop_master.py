from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CropMasterBase(BaseModel):
    crop_code: str = Field(..., min_length=2, max_length=50)
    crop_name: str = Field(..., min_length=2, max_length=150)
    crop_category: Optional[str] = None
    unit: str = "Kg"


class CropMasterCreate(CropMasterBase):
    pass


class CropMasterUpdate(BaseModel):
    crop_code: Optional[str] = None
    crop_name: Optional[str] = None
    crop_category: Optional[str] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None


class CropMasterResponse(CropMasterBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True