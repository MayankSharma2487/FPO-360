from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountOut, AccountStatus, AccountUpdate
from app.services.account_service import AccountService

router = APIRouter(prefix="/finance/accounts", tags=["Chart of Accounts"])
READ = ("Super Admin", "FPO Admin", "Accountant", "Manager", "Viewer")
WRITE = ("Super Admin", "FPO Admin", "Accountant")


@router.get("", response_model=list[AccountOut])
def accounts(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return AccountService(db).accounts(user)


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(p: AccountCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return AccountService(db).save_account(user, p)


@router.get("/{id}", response_model=AccountOut)
def account(id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return AccountService(db).account(user, id)


@router.put("/{id}", response_model=AccountOut)
def update_account(id: int, p: AccountUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return AccountService(db).save_account(user, p, id)


@router.patch("/{id}/status", response_model=AccountOut)
def account_status(id: int, p: AccountStatus, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return AccountService(db).set_account_status(user, id, p.is_active)
