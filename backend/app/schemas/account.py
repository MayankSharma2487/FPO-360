from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
AccountType = Literal["Asset", "Liability", "Equity", "Income", "Expense"]
class AccountCreate(BaseModel):
    account_code: str = Field(min_length=1, max_length=20); account_name: str = Field(min_length=1, max_length=150); account_type: AccountType; account_group: str = Field(min_length=1, max_length=100); account_subtype: Literal["CASH", "BANK"] | None = None
class AccountUpdate(AccountCreate): pass
class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; organization_id: int; account_code: str; account_name: str; account_type: str; account_group: str; account_subtype: str | None; system_key: str | None; is_active: bool
class AccountStatus(BaseModel): is_active: bool
