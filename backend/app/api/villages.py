from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.village import VillageCreate, VillageUpdate, VillageResponse
from app.services.village_service import VillageService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/villages",
    tags=["Villages"]
)


@router.post("/", response_model=VillageResponse, status_code=status.HTTP_201_CREATED)
def create_village(
    payload: VillageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = VillageService(db)
    return service.create_village(payload, current_user)


@router.get("/", response_model=list[VillageResponse])
def list_villages(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = VillageService(db)
    return service.list_villages(current_user)


@router.get("/{village_id}", response_model=VillageResponse)
def get_village(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = VillageService(db)
    village = service.repo.get_by_id(village_id)  # direct access for simplicity
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
    if current_user.role.name != "Super Admin" and village.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return village


@router.put("/{village_id}", response_model=VillageResponse)
def update_village(
    village_id: int,
    payload: VillageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = VillageService(db)
    return service.update_village(village_id, payload, current_user)


@router.patch("/{village_id}/status", response_model=VillageResponse)
def toggle_village_status(
    village_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = VillageService(db)
    return service.toggle_village_status(village_id, is_active, current_user)