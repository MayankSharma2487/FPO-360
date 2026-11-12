from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.services.finance_setup_service import FinanceSetupService
from app.services.account_service import AccountService

router = APIRouter(prefix="/finance/setup", tags=["Finance Setup"])
READ = ("Super Admin", "FPO Admin", "Accountant", "Manager", "Viewer")
WRITE = ("Super Admin", "FPO Admin", "Accountant")


@router.get("/status")
def setup_status(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return FinanceSetupService(db).setup_status(user)


@router.get("")
def setup_preview(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return AccountService(db).accounts(user)


@router.post("")
def setup(db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return FinanceSetupService(db).setup(user)
