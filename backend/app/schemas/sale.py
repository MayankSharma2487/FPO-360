from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from decimal import Decimal


class SaleBase(BaseModel):
    sale_date: datetime
    customer_id: int
    crop_id: int
    quantity: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6, description="Requests use the selected unit; responses return the stored item-base quantity")
    unit: str = Field(default="KG", description="A unit dimensionally compatible with the selected item's base unit")
    rate_per_unit: Decimal = Field(..., gt=0)
    payment_status: str = Field(default="Pending", description="Pending or Paid")
    remarks: Optional[str] = Field(None, max_length=500)


class SaleCreate(SaleBase):
    organization_id: Optional[int] = None


class SaleUpdate(BaseModel):
    sale_date: Optional[datetime] = None
    customer_id: Optional[int] = None
    crop_id: Optional[int] = None
    quantity: Optional[Decimal] = Field(None, gt=0, max_digits=20, decimal_places=6)
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
    item_type: Optional[str] = None
    base_unit: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer("quantity", when_used="json")
    def serialize_quantity_as_number(self, value: Decimal):
        return float(value)
