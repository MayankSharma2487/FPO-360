from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.finance_report import GeneralLedgerOut, TrialBalanceOut
from app.services.finance_report_service import FinanceReportService

router = APIRouter(prefix="/finance/reports", tags=["Finance Reports"])
READ = ("Super Admin", "FPO Admin", "Accountant", "Manager", "Viewer")


@router.get("/general-ledger", response_model=GeneralLedgerOut)
def general_ledger(account_id: int, start_date: date | None = None, end_date: date | None = None,
                   db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return FinanceReportService(db).general_ledger(user, account_id, start_date, end_date)


@router.get("/trial-balance", response_model=TrialBalanceOut)
def trial_balance(financial_year_id: int, as_on_date: date, include_zero: bool = False,
                  db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return FinanceReportService(db).trial_balance(user, financial_year_id, as_on_date, include_zero)
