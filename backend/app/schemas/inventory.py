from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


TransactionType = Literal["IN", "OUT"]


class InventoryAdjustRequest(BaseModel):
    crop_id: int = Field(..., gt=0)
    transaction_type: TransactionType
    quantity: float = Field(..., gt=0, description="Positive magnitude in KG")
    remarks: Optional[str] = Field(None, max_length=500)


class InventoryLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    crop_id: int
    crop_name: Optional[str] = None
    transaction_type: str
    quantity: float
    reference_type: str
    reference_id: Optional[int] = None
    remarks: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class InventoryBalanceResponse(BaseModel):
    crop_id: int
    crop_name: Optional[str] = None
    total_in: float
    total_out: float
    current_balance: float