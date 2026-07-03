from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class ProcurementBase(BaseModel):
    """Base schema for procurement data"""
    procurement_date: datetime
    farmer_id: int
    crop_id: int
    quantity: float = Field(..., gt=0, description="User-entered quantity (will be converted to KG by backend)")
    unit: str = Field(default="KG", description="Unit of measurement: KG, QUINTAL, or TON")
    rate_per_unit: Decimal = Field(..., gt=0, description="Price per unit (using user-entered unit, not KG)")
    quality_grade: Optional[str] = Field(None, description="Quality grade: A, B, C, or D")
    remarks: Optional[str] = Field(None, description="Additional remarks")


class ProcurementCreate(ProcurementBase):
    """Schema for creating new procurement record"""
    organization_id: Optional[int] = Field(None, description="Organization ID (optional, defaults to current user's org)")


class ProcurementUpdate(BaseModel):
    """Schema for updating procurement record - all fields optional"""
    procurement_date: Optional[datetime] = None
    quantity: Optional[float] = Field(None, gt=0, description="User-entered quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement (KG/QUINTAL/TON)")
    rate_per_unit: Optional[Decimal] = Field(None, gt=0)
    quality_grade: Optional[str] = Field(None, description="A, B, C, or D")
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class ProcurementResponse(ProcurementBase):
    """Schema for API response - includes stored data"""
    id: int
    procurement_no: str
    organization_id: int
    total_amount: Decimal = Field(..., description="Total amount calculated from user-entered quantity × rate_per_unit")
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    farmer_name: Optional[str] = None
    crop_name: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "procurement_no": "PR-2026-00001",
                "procurement_date": "2026-06-30T00:00:00",
                "farmer_id": 1,
                "farmer_name": "John Farmer",
                "crop_id": 5,
                "crop_name": "Wheat",
                "quantity": 500,
                "unit": "KG",
                "rate_per_unit": "25.00",
                "total_amount": "12500.00",
                "quality_grade": "A",
                "remarks": "Good quality produce",
                "organization_id": 1,
                "is_active": True,
                "created_at": "2026-06-30T10:30:00",
                "updated_at": "2026-06-30T10:30:00"
            }
        }