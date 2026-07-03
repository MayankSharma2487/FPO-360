from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.crop_master import CropMasterCreate, CropMasterUpdate, CropMasterResponse
from app.services.crop_master_service import CropMasterService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/crop-masters",
    tags=["Crop Masters"]
)


@router.post("/", response_model=CropMasterResponse, status_code=status.HTTP_201_CREATED)
def create_crop_master(
    payload: CropMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = CropMasterService(db)
    return service.create_crop_master(payload)


@router.get("/", response_model=list[CropMasterResponse])
def list_crop_masters(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"))
):
    service = CropMasterService(db)
    return service.list_crop_masters()


@router.put("/{crop_id}", response_model=CropMasterResponse)
def update_crop_master(
    crop_id: int,
    payload: CropMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = CropMasterService(db)
    return service.update_crop_master(crop_id, payload)


@router.patch("/{crop_id}/status", response_model=CropMasterResponse)
def toggle_crop_master_status(
    crop_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = CropMasterService(db)
    return service.toggle_status(crop_id, is_active)