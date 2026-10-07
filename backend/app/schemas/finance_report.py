from datetime import date
from decimal import Decimal
from pydantic import BaseModel
class LedgerLine(BaseModel): date: date; journal_no: str; narration: str; debit: Decimal; credit: Decimal; running_balance: Decimal; balance_side: str
class GeneralLedgerOut(BaseModel): account_id: int; account_code: str; account_name: str; opening_balance: Decimal; opening_balance_side: str; lines: list[LedgerLine]; debit_total: Decimal; credit_total: Decimal; closing_balance: Decimal; closing_balance_side: str
class TrialBalanceLine(BaseModel): account_id: int; account_code: str; account_name: str; debit: Decimal; credit: Decimal
class TrialBalanceOut(BaseModel): financial_year_id: int; as_on_date: date; accounts: list[TrialBalanceLine]; debit_total: Decimal; credit_total: Decimal
