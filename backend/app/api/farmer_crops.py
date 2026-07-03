from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.farmer_crop import FarmerCropCreate, FarmerCropUpdate, FarmerCropResponse
from app.services.farmer_crop_service import FarmerCropService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/farmer-crops",
    tags=["Farmer Crops"]
)


@router.post("/", response_model=FarmerCropResponse, status_code=status.HTTP_201_CREATED)
def create_farmer_crop(
    payload: FarmerCropCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = FarmerCropService(db)
    return service.create_farmer_crop(payload, current_user)


@router.get("/", response_model=list[FarmerCropResponse])
def list_farmer_crops(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = FarmerCropService(db)
    return service.list_farmer_crops(current_user)


@router.put("/{record_id}", response_model=FarmerCropResponse)
def update_farmer_crop(
    record_id: int,
    payload: FarmerCropUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = FarmerCropService(db)
    return service.update_farmer_crop(record_id, payload, current_user)


@router.patch("/{record_id}/status", response_model=FarmerCropResponse)
def toggle_farmer_crop_status(
    record_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager"))
):
    service = FarmerCropService(db)
    return service.toggle_status(record_id, is_active, current_user)