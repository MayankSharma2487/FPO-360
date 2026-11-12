from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.journal import JournalCreate, JournalOut, JournalVoid
from app.services.journal_service import JournalService

router = APIRouter(prefix="/finance/journals", tags=["Journals"])
READ = ("Super Admin", "FPO Admin", "Accountant", "Manager", "Viewer")
WRITE = ("Super Admin", "FPO Admin", "Accountant")


@router.get("", response_model=list[JournalOut])
def journals(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return JournalService(db).journals(user)


@router.post("", response_model=JournalOut, status_code=status.HTTP_201_CREATED)
def create_journal(p: JournalCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return JournalService(db).create_journal(user, p)


@router.get("/{id}", response_model=JournalOut)
def journal(id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return JournalService(db).journal(user, id)


@router.patch("/{id}/void", response_model=JournalOut)
def void_journal(id: int, p: JournalVoid, db: Session = Depends(get_db), user: User = Depends(require_roles(*WRITE))):
    return JournalService(db).void(user, id, p.void_reason)
