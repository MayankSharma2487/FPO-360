from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class SaleBase(BaseModel):
    sale_date: datetime
    customer_id: int
    crop_id: int
    quantity: float = Field(..., gt=0, description="User-entered quantity (converted to KG by backend)")
    unit: str = Field(default="KG", description="KG, QUINTAL, or TON")
    rate_per_unit: Decimal = Field(..., gt=0)
    payment_status: str = Field(default="Pending", description="Pending or Paid")
    remarks: Optional[str] = Field(None, max_length=500)


class SaleCreate(SaleBase):
    organization_id: Optional[int] = None


class SaleUpdate(BaseModel):
    sale_date: Optional[datetime] = None
    customer_id: Optional[int] = None
    crop_id: Optional[int] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    rate_per_unit: Optional[Decimal] = Field(None, gt=0)
    payment_status: Optional[str] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class SaleResponse(SaleBase):
    id: int
    sale_no: str
    organization_id: int
    total_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    customer_name: Optional[str] = None
    crop_name: Optional[str] = None

    class Config:
        from_attributes = True
