from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.crop_master import CropMaster
from app.repositories.crop_master_repository import CropMasterRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.crop_master import CropMasterCreate, CropMasterUpdate


class CropMasterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CropMasterRepository(db)
        self.org_repo = OrganizationRepository(db)

    def create_crop_master(self, payload: CropMasterCreate) -> CropMaster:
        existing = self.repo.get_by_code(payload.crop_code)
        if existing:
            raise HTTPException(status_code=400, detail="Crop code already exists")

        crop = CropMaster(**payload.model_dump())
        return self.repo.create(crop)

    def update_crop_master(self, crop_id: int, payload: CropMasterUpdate) -> CropMaster:
        crop = self.repo.get_by_id(crop_id)
        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found")
        update_data = payload.model_dump(exclude_unset=True)
        return self.repo.update(crop, update_data)

    def toggle_status(self, crop_id: int, is_active: bool) -> CropMaster:
        crop = self.repo.get_by_id(crop_id)
        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found")
        return self.repo.toggle_active(crop, is_active)

    def list_crop_masters(self):
        return self.repo.list_all()
