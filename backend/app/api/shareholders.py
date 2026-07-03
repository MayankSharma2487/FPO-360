from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.shareholder import ShareholderCreate, ShareholderUpdate, ShareholderResponse
from app.services.shareholder_service import ShareholderService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/shareholders",
    tags=["Shareholders"]
)


@router.post("/", response_model=ShareholderResponse, status_code=status.HTTP_201_CREATED)
def create_shareholder(
    payload: ShareholderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = ShareholderService(db)
    return service.create_shareholder(payload, current_user)


@router.get("/", response_model=list[ShareholderResponse])
def list_shareholders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = ShareholderService(db)
    return service.list_shareholders(current_user)


@router.get("/{shareholder_id}", response_model=ShareholderResponse)
def get_shareholder(
    shareholder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = ShareholderService(db)
    shareholder = service.repo.get_by_id(shareholder_id)
    if not shareholder:
        raise HTTPException(status_code=404, detail="Shareholder not found")
    if current_user.role.name != "Super Admin" and shareholder.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return shareholder


@router.put("/{shareholder_id}", response_model=ShareholderResponse)
def update_shareholder(
    shareholder_id: int,
    payload: ShareholderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = ShareholderService(db)
    return service.update_shareholder(shareholder_id, payload, current_user)


@router.patch("/{shareholder_id}/status", response_model=ShareholderResponse)
def toggle_shareholder_status(
    shareholder_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = ShareholderService(db)
    return service.toggle_status(shareholder_id, is_active, current_user)