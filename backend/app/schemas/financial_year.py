from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

class FinancialYearCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    @model_validator(mode="after")
    def valid_range(self):
        if self.end_date <= self.start_date: raise ValueError("end_date must be after start_date")
        if (self.start_date.month, self.start_date.day) != (4, 1) or (self.end_date.month, self.end_date.day) != (3, 31) or self.end_date.year != self.start_date.year + 1:
            raise ValueError("Financial years must run from 1 April through 31 March")
        return self
class FinancialYearUpdate(FinancialYearCreate): pass
class FinancialYearOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; organization_id: int; name: str; start_date: date; end_date: date; is_current: bool; is_locked: bool; locked_at: datetime | None
