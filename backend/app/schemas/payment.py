from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaymentCreate(BaseModel):
    farmer_id: int
    procurement_id: int
    amount: float
    payment_date: datetime
    payment_method: str
    reference_no: Optional[str] = None
    status: str
    remarks: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    reference_no: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    payment_no: str
    organization_id: int
    farmer_id: int
    procurement_id: int
    amount: float
    payment_date: datetime
    payment_method: str
    reference_no: Optional[str] = None
    status: str
    remarks: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Display fields populated by the payment router
    farmer_name: Optional[str] = None
    procurement_no: Optional[str] = None
    crop_name: Optional[str] = None
    procurement_total: Optional[float] = None
    procurement_qty: Optional[float] = None

    class Config:
        from_attributes = True