from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class VillageBase(BaseModel):
    village_name: str
    block: Optional[str] = None
    district: str
    state: str


class VillageCreate(VillageBase):
    village_code: Optional[str] = None
    organization_id: Optional[int] = None


class VillageUpdate(BaseModel):
    village_code: Optional[str] = Field(None, min_length=2, max_length=50)
    village_name: Optional[str] = Field(None, min_length=2, max_length=150)
    district: Optional[str] = None
    state: Optional[str] = None
    is_active: Optional[bool] = None


class VillageResponse(VillageBase):
    id: int
    village_code: str
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True