from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.item_catalogue import BaseUnit, ItemType


class ItemCreate(BaseModel):
    item_name: str = Field(..., min_length=2, max_length=150)
    item_type: ItemType
    category: Optional[str] = Field(None, max_length=100)
    base_unit: BaseUnit
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("item_name")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class ItemUpdate(BaseModel):
    item_name: Optional[str] = Field(None, min_length=2, max_length=150)
    item_type: Optional[ItemType] = None
    category: Optional[str] = Field(None, max_length=100)
    base_unit: Optional[BaseUnit] = None
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("item_name")
    @classmethod
    def non_blank_if_set(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            raise ValueError("Value cannot be blank")
        return value.strip()

    @field_validator("item_type", "base_unit")
    @classmethod
    def non_null_catalogue_fields(cls, value):
        if value is None:
            raise ValueError("Value cannot be null")
        return value


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_code: str
    item_name: str
    item_type: ItemType
    category: Optional[str] = None
    base_unit: BaseUnit
    description: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Legacy aliases remain in responses for existing crop-facing clients.
    crop_code: str
    crop_name: str
    crop_category: Optional[str] = None
    unit: str
