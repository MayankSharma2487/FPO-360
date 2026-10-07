from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
class JournalLineIn(BaseModel):
    account_id: int; debit: Decimal = Decimal("0"); credit: Decimal = Decimal("0"); party_type: Literal["FARMER", "CUSTOMER"] | None = None; party_id: int | None = None; line_narration: str | None = None
    @field_validator("debit", "credit")
    @classmethod
    def precision(cls, v):
        if v < 0 or v.as_tuple().exponent < -2 or (v != 0 and v.adjusted() >= 12): raise ValueError("Amounts must fit a positive monetary value with at most 2 decimal places")
        return v
class JournalCreate(BaseModel):
    entry_date: date; financial_year_id: int; narration: str = Field(min_length=1); source_type: Literal["MANUAL", "OPENING"] = "MANUAL"; lines: list[JournalLineIn]
    @field_validator("lines")
    @classmethod
    def valid_lines(cls, lines):
        if any((line.debit > 0) == (line.credit > 0) for line in lines):
            raise ValueError("Each line must have exactly one positive debit or credit")
        return lines
class JournalVoid(BaseModel): void_reason: str = Field(min_length=1, max_length=1000)
class JournalLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; line_no: int; account_id: int; debit: Decimal; credit: Decimal; party_type: str | None; party_id: int | None; line_narration: str | None
class JournalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; organization_id: int; journal_no: str; entry_date: date; financial_year_id: int; narration: str; source_type: str; source_id: int | None; status: str; created_at: datetime; voided_by: int | None = None; voided_at: datetime | None = None; void_reason: str | None = None; lines: list[JournalLineOut]
