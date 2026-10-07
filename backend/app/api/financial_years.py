from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.financial_year import FinancialYearCreate, FinancialYearOut, FinancialYearUpdate
from app.services.financial_year_service import FinancialYearService

router = APIRouter(prefix="/finance/years", tags=["Financial Years"])
READ = ("Super Admin", "FPO Admin", "Accountant", "Manager", "Viewer")
WRITE = ("Super Admin", "FPO Admin", "Accountant")


@router.get("", response_model=list[FinancialYearOut])
def years(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return FinancialYearService(db).list_years(user)


@router.post("", response_model=FinancialYearOut, status_code=status.HTTP_201_CREATED)
def create_year(p: FinancialYearCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return FinancialYearService(db).save_year(user, p)


@router.put("/{id}", response_model=FinancialYearOut)
def update_year(id: int, p: FinancialYearUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return FinancialYearService(db).save_year(user, p, id)


@router.patch("/{id}/current", response_model=FinancialYearOut)
def current_year(id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return FinancialYearService(db).set_current(user, id)


@router.patch("/{id}/lock", response_model=FinancialYearOut)
def lock_year(id: int, locked: bool = True, db: Session = Depends(get_db), user: User = Depends(require_roles("Super Admin", "FPO Admin"))):
    return FinancialYearService(db).lock_year(user, id, locked)
