from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.farmer import FarmerCreate, FarmerUpdate, FarmerResponse
from app.services.farmer_service import FarmerService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/farmers",
    tags=["Farmers"]
)


@router.post("/", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
def create_farmer(
    payload: FarmerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = FarmerService(db)
    return service.create_farmer(payload, current_user)


@router.get("/", response_model=list[FarmerResponse])
def list_farmers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = FarmerService(db)
    return service.list_farmers(current_user)


@router.get("/{farmer_id}", response_model=FarmerResponse)
def get_farmer(
    farmer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = FarmerService(db)
    farmer = service.repo.get_by_id(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if current_user.role.name != "Super Admin" and farmer.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return farmer


@router.put("/{farmer_id}", response_model=FarmerResponse)
def update_farmer(
    farmer_id: int,
    payload: FarmerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = FarmerService(db)
    return service.update_farmer(farmer_id, payload, current_user)


@router.patch("/{farmer_id}/status", response_model=FarmerResponse)
def toggle_farmer_status(
    farmer_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = FarmerService(db)
    return service.toggle_farmer_status(farmer_id, is_active, current_user)