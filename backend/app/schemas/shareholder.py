from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from datetime import date


class ShareholderBase(BaseModel):
    share_certificate_no: Optional[str] = None
    share_count: int = Field(..., gt=0)
    share_value: Decimal = Field(..., gt=0)
    joining_date: Optional[datetime] = None
    is_active: bool = True
    shareholder_no: Optional[str] = None


class ShareholderCreate(ShareholderBase):
    farmer_id: int
    organization_id: Optional[int] = None


class ShareholderUpdate(BaseModel):
    share_certificate_no: Optional[str] = None
    share_count: Optional[int] = Field(None, gt=0)
    share_value: Optional[Decimal] = Field(None, gt=0)
    joining_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class ShareholderResponse(BaseModel):
    id: int
    shareholder_no: str
    share_certificate_no: str
    share_count: int
    share_value: Decimal
    total_share_capital: Decimal
    joining_date: date
    is_active: bool

    farmer_id: int
    organization_id: int

    created_at: datetime
    updated_at: Optional[datetime] = None

    farmer_name: Optional[str] = None
    farmer_mobile: Optional[str] = None

    class Config:
        from_attributes = True