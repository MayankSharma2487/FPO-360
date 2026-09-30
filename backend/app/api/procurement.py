from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.procurement import ProcurementCreate, ProcurementUpdate, ProcurementResponse
from app.services.procurement_service import ProcurementService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/procurements",
    tags=["Procurement"]
)


@router.post("/", response_model=ProcurementResponse, status_code=status.HTTP_201_CREATED)
def create_procurement(
    payload: ProcurementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = ProcurementService(db)
    return service.create_procurement(payload, current_user)


@router.get("/", response_model=list[ProcurementResponse])
def list_procurements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = ProcurementService(db)
    return service.list_procurements(current_user)


@router.put("/{record_id}", response_model=ProcurementResponse)
def update_procurement(
    record_id: int,
    payload: ProcurementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = ProcurementService(db)
    return service.update_procurement(record_id, payload, current_user)


@router.patch("/{record_id}/status", response_model=ProcurementResponse)
def toggle_procurement_status(
    record_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = ProcurementService(db)
    return service.toggle_procurement_status(record_id, is_active, current_user)