from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.domain.item_catalogue import BaseUnit


class ProductionInputCreate(BaseModel):
    item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    unit: BaseUnit


class ProductionCreate(BaseModel):
    production_date: date
    finished_item_id: int = Field(gt=0)
    output_quantity: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    output_unit: BaseUnit
    inputs: list[ProductionInputCreate] = Field(min_length=1, max_length=100)
    wastage_quantity: Decimal = Field(default=Decimal("0"), ge=0, max_digits=20, decimal_places=6)
    wastage_unit: BaseUnit
    notes: Optional[str] = Field(None, max_length=1000)


class ProductionInputResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    item_type: str
    quantity: Decimal
    unit: BaseUnit
    base_quantity: Decimal
    base_unit: BaseUnit


class ProductionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_no: str
    production_date: date
    finished_item_id: int
    finished_item_name: str
    output_quantity: Decimal
    output_unit: BaseUnit
    output_base_quantity: Decimal
    base_unit: BaseUnit
    wastage_quantity: Decimal
    wastage_unit: BaseUnit
    wastage_base_quantity: Decimal
    total_input_consumption: list[dict]
    inputs: list[ProductionInputResponse]
    status: str
    notes: Optional[str]
    created_by: Optional[int]
    created_at: datetime


class ProductionListResponse(ProductionResponse):
    pass
