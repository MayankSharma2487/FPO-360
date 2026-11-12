from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.item_catalogue import BaseUnit, ItemType


TransactionType = Literal["IN", "OUT"]


class InventoryAdjustRequest(BaseModel):
    crop_id: Optional[int] = Field(None, gt=0, description="Legacy agricultural item identifier")
    item_id: Optional[int] = Field(None, gt=0, description="Catalogue item identifier")
    transaction_type: TransactionType
    quantity: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6)
    unit: Optional[BaseUnit] = None
    remarks: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def one_matching_item_reference(self):
        if self.item_id is None and self.crop_id is None:
            raise ValueError("item_id or crop_id is required")
        if self.item_id is not None and self.crop_id is not None and self.item_id != self.crop_id:
            raise ValueError("item_id and crop_id must refer to the same catalogue item")
        return self


class InventoryLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    item_id: int
    item_name: Optional[str] = None
    item_type: Optional[ItemType] = None
    base_unit: Optional[BaseUnit] = None
    crop_id: Optional[int] = None
    crop_name: Optional[str] = None
    transaction_type: TransactionType
    quantity: Decimal
    reference_type: str
    reference_id: Optional[int] = None
    idempotency_key: Optional[str] = None
    reverses_id: Optional[int] = None
    source_revision: int = 1
    remarks: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class InventoryBalanceResponse(BaseModel):
    item_id: int
    item_name: str
    item_type: ItemType
    base_unit: BaseUnit
    total_in: Decimal
    total_out: Decimal
    current_balance: Decimal
    crop_id: Optional[int] = None
    crop_name: Optional[str] = None


class InventoryReconciliationResponse(BaseModel):
    organization_id: int
    item_id: int
    item_name: str
    balance_quantity: Decimal
    ledger_quantity: Decimal
    difference: Decimal
